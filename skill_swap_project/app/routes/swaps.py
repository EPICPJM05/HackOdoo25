from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..models import SwapRequest, User, UserSkill, Feedback
from .. import db, socketio
from datetime import datetime

swaps_bp = Blueprint('swaps', __name__)

@swaps_bp.route('/swaps')
@login_required
def my_swaps():
    """View user's swap requests"""
    # Get all swap requests for the user
    all_swaps = SwapRequest.get_user_requests(current_user.id)
    
    # Separate by status
    pending_received = SwapRequest.get_pending_requests(current_user.id)
    active_swaps = SwapRequest.get_active_swaps(current_user.id)
    completed_swaps = SwapRequest.get_completed_swaps(current_user.id)
    
    # Get pending requests sent by user
    pending_sent = SwapRequest.query.filter_by(
        requester_id=current_user.id,
        status='pending'
    ).all()
    
    return render_template('swaps/my_swaps.html',
                         pending_received=pending_received,
                         pending_sent=pending_sent,
                         active_swaps=active_swaps,
                         completed_swaps=completed_swaps,
                         all_swaps=all_swaps)

@swaps_bp.route('/swap/request', methods=['POST'])
@login_required
def send_swap_request():
    """Send a swap request to another user"""
    receiver_id = request.form.get('receiver_id', type=int)
    requester_skill = request.form.get('requester_skill', '').strip()
    receiver_skill = request.form.get('receiver_skill', '').strip()
    message = request.form.get('message', '').strip()
    
    # Validation
    if not receiver_id or not requester_skill or not receiver_skill:
        flash('All fields are required', 'error')
        return redirect(url_for('users.view_user', user_id=receiver_id))
    
    # Check if receiver exists and is not banned
    receiver = User.query.get(receiver_id)
    if not receiver or receiver.is_banned:
        flash('Invalid user', 'error')
        return redirect(url_for('users.search_users'))
    
    # Check if user is trying to swap with themselves
    if receiver_id == current_user.id:
        flash('You cannot swap with yourself', 'error')
        return redirect(url_for('users.view_user', user_id=receiver_id))
    
    # Check if receiver is available for swaps
    if not receiver.is_available_for_swaps():
        flash('This user is not available for new swap requests', 'error')
        return redirect(url_for('users.view_user', user_id=receiver_id))
    
    # Check if requester has the skill they're offering
    requester_has_skill = UserSkill.query.filter_by(
        user_id=current_user.id,
        skill_name=requester_skill,
        skill_type='offered'
    ).first()
    
    if not requester_has_skill:
        flash('You must have the skill you are offering in your offered skills', 'error')
        return redirect(url_for('users.view_user', user_id=receiver_id))
    
    # Check if receiver has the skill they're offering
    receiver_has_skill = UserSkill.query.filter_by(
        user_id=receiver_id,
        skill_name=receiver_skill,
        skill_type='offered'
    ).first()
    
    if not receiver_has_skill:
        flash('The other user must have the skill they are offering', 'error')
        return redirect(url_for('users.view_user', user_id=receiver_id))
    
    # Check if there's already a pending request
    existing_request = SwapRequest.query.filter_by(
        requester_id=current_user.id,
        receiver_id=receiver_id,
        status='pending'
    ).first()
    
    if existing_request:
        flash('You already have a pending swap request with this user', 'error')
        return redirect(url_for('users.view_user', user_id=receiver_id))
    
    # Create swap request
    swap_request = SwapRequest(
        requester_id=current_user.id,
        receiver_id=receiver_id,
        requester_skill=requester_skill,
        receiver_skill=receiver_skill,
        message=message if message else None
    )
    
    db.session.add(swap_request)
    db.session.commit()
    
    # Emit real-time notification
    socketio.emit('new_swap_request', {
        'receiver_id': receiver_id,
        'requester_name': current_user.name,
        'message': f'New swap request from {current_user.name}'
    }, room=f'user_{receiver_id}')
    
    flash('Swap request sent successfully!', 'success')
    return redirect(url_for('swaps.my_swaps'))

@swaps_bp.route('/swap/<int:swap_id>/accept', methods=['POST'])
@login_required
def accept_swap(swap_id):
    """Accept a swap request"""
    swap_request = SwapRequest.query.get_or_404(swap_id)
    
    # Check if current user can respond to this request
    if not swap_request.can_be_responded_by(current_user.id):
        flash('You can only respond to swap requests sent to you', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    if swap_request.status != 'pending':
        flash('This swap request has already been processed', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    # Accept the swap
    swap_request.accept()
    db.session.commit()
    
    # Emit real-time notification
    socketio.emit('swap_accepted', {
        'requester_id': swap_request.requester_id,
        'receiver_name': current_user.name,
        'message': f'Your swap request has been accepted by {current_user.name}'
    }, room=f'user_{swap_request.requester_id}')
    
    flash('Swap request accepted!', 'success')
    return redirect(url_for('swaps.my_swaps'))

@swaps_bp.route('/swap/<int:swap_id>/reject', methods=['POST'])
@login_required
def reject_swap(swap_id):
    """Reject a swap request"""
    swap_request = SwapRequest.query.get_or_404(swap_id)
    
    # Check if current user can respond to this request
    if not swap_request.can_be_responded_by(current_user.id):
        flash('You can only respond to swap requests sent to you', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    if swap_request.status != 'pending':
        flash('This swap request has already been processed', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    # Reject the swap
    swap_request.reject()
    db.session.commit()
    
    # Emit real-time notification
    socketio.emit('swap_rejected', {
        'requester_id': swap_request.requester_id,
        'receiver_name': current_user.name,
        'message': f'Your swap request has been rejected by {current_user.name}'
    }, room=f'user_{swap_request.requester_id}')
    
    flash('Swap request rejected', 'info')
    return redirect(url_for('swaps.my_swaps'))

@swaps_bp.route('/swap/<int:swap_id>/cancel', methods=['POST'])
@login_required
def cancel_swap(swap_id):
    """Cancel a swap request (only requester can do this)"""
    swap_request = SwapRequest.query.get_or_404(swap_id)
    
    # Check if current user can cancel this request
    if not swap_request.can_be_cancelled_by(current_user.id):
        flash('You can only cancel your own pending swap requests', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    if swap_request.status != 'pending':
        flash('Only pending swap requests can be cancelled', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    # Cancel the swap
    swap_request.cancel()
    db.session.commit()
    
    flash('Swap request cancelled', 'info')
    return redirect(url_for('swaps.my_swaps'))

@swaps_bp.route('/swap/<int:swap_id>/complete', methods=['POST'])
@login_required
def complete_swap(swap_id):
    """Mark a swap as completed"""
    swap_request = SwapRequest.query.get_or_404(swap_id)
    
    # Check if current user participated in this swap
    if swap_request.requester_id != current_user.id and swap_request.receiver_id != current_user.id:
        flash('You can only complete swaps you participated in', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    if swap_request.status != 'accepted':
        flash('Only accepted swaps can be marked as completed', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    # Complete the swap
    swap_request.complete()
    db.session.commit()
    
    flash('Swap marked as completed! You can now provide feedback.', 'success')
    return redirect(url_for('swaps.my_swaps'))

@swaps_bp.route('/swap/<int:swap_id>')
@login_required
def view_swap(swap_id):
    """View details of a specific swap"""
    swap_request = SwapRequest.query.get_or_404(swap_id)
    
    # Check if current user participated in this swap
    if swap_request.requester_id != current_user.id and swap_request.receiver_id != current_user.id:
        flash('You can only view swaps you participated in', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    # Get the other participant
    other_user_id = swap_request.receiver_id if swap_request.requester_id == current_user.id else swap_request.requester_id
    other_user = User.query.get(other_user_id)
    
    # Get feedback for this swap
    feedback = Feedback.get_swap_feedback(swap_id)
    
    # Check if current user can rate this swap
    can_rate = Feedback.can_user_rate_swap(current_user.id, swap_id)
    
    return render_template('swaps/view_swap.html',
                         swap=swap_request,
                         other_user=other_user,
                         feedback=feedback,
                         can_rate=can_rate)

# API endpoints for real-time updates
@swaps_bp.route('/api/swaps/pending-count')
@login_required
def get_pending_count():
    """Get count of pending swap requests"""
    count = SwapRequest.get_pending_requests(current_user.id).count()
    return jsonify({'count': count})

@swaps_bp.route('/api/swaps/active-count')
@login_required
def get_active_count():
    """Get count of active swaps"""
    count = len(SwapRequest.get_active_swaps(current_user.id))
    return jsonify({'count': count})

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    if current_user.is_authenticated:
        socketio.join_room(f'user_{current_user.id}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    if current_user.is_authenticated:
        socketio.leave_room(f'user_{current_user.id}') 