from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..models import SwapRequest, User, UserSkill, Feedback
from .. import db, socketio
from datetime import datetime
from flask_socketio import join_room, leave_room

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
                         all_swaps=all_swaps,
                         Feedback=Feedback)

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
    
    # Create a system message for the chat
    from ..models.chat import ChatMessage
    system_message = ChatMessage(
        swap_id=swap_id,
        sender_id=swap_request.receiver_id,  # Use receiver as sender for system message
        message=f"Swap accepted! You can now chat to coordinate your skill exchange.",
        message_type='system'
    )
    db.session.add(system_message)
    db.session.commit()
    
    # Emit real-time notification
    socketio.emit('swap_accepted', {
        'requester_id': swap_request.requester_id,
        'receiver_name': current_user.name,
        'message': f'Your swap request has been accepted by {current_user.name}'
    }, room=f'user_{swap_request.requester_id}')
    
    flash('Swap request accepted! You can now chat with the other user.', 'success')
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
    pending_requests = SwapRequest.get_pending_requests(current_user.id)
    count = len(pending_requests)
    return jsonify({'count': count})

@swaps_bp.route('/api/swaps/active-count')
@login_required
def get_active_count():
    """Get count of active swaps"""
    count = len(SwapRequest.get_active_swaps(current_user.id))
    return jsonify({'count': count})

@socketio.on('connect')
def handle_connect(auth):
    """Handle WebSocket connection"""
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')

@socketio.on('disconnect')
def handle_disconnect(auth):
    """Handle WebSocket disconnection"""
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')

# Chat routes
@swaps_bp.route('/swap/<int:swap_id>/chat')
@login_required
def chat(swap_id):
    """Chat interface for an accepted swap"""
    swap_request = SwapRequest.query.get_or_404(swap_id)
    
    # Check if current user participated in this swap
    if swap_request.requester_id != current_user.id and swap_request.receiver_id != current_user.id:
        flash('You can only chat in swaps you participated in', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    # Check if swap is accepted (only accepted swaps can have chat)
    if swap_request.status != 'accepted':
        flash('Chat is only available for accepted swaps', 'error')
        return redirect(url_for('swaps.view_swap', swap_id=swap_id))
    
    # Get the other participant
    other_user_id = swap_request.receiver_id if swap_request.requester_id == current_user.id else swap_request.requester_id
    other_user = User.query.get(other_user_id)
    
    # Get recent messages
    from ..models.chat import ChatMessage
    messages = ChatMessage.get_swap_messages(swap_id, limit=100)
    
    return render_template('swaps/chat.html',
                         swap=swap_request,
                         other_user=other_user,
                         messages=messages)

@swaps_bp.route('/api/swap/<int:swap_id>/messages', methods=['GET'])
@login_required
def get_messages(swap_id):
    """Get messages for a swap"""
    swap_request = SwapRequest.query.get_or_404(swap_id)
    
    # Check if current user participated in this swap
    if swap_request.requester_id != current_user.id and swap_request.receiver_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if swap is accepted
    if swap_request.status != 'accepted':
        return jsonify({'error': 'Chat not available'}), 400
    
    from ..models.chat import ChatMessage
    messages = ChatMessage.get_swap_messages(swap_id, limit=100)
    
    return jsonify({
        'messages': [msg.to_dict() for msg in messages]
    })

@swaps_bp.route('/api/swap/<int:swap_id>/messages', methods=['POST'])
@login_required
def send_message(swap_id):
    """Send a message in a swap chat"""
    swap_request = SwapRequest.query.get_or_404(swap_id)
    
    # Check if current user participated in this swap
    if swap_request.requester_id != current_user.id and swap_request.receiver_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if swap is accepted
    if swap_request.status != 'accepted':
        return jsonify({'error': 'Chat not available'}), 400
    
    message_text = request.json.get('message', '').strip()
    if not message_text:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    from ..models.chat import ChatMessage
    message = ChatMessage(
        swap_id=swap_id,
        sender_id=current_user.id,
        message=message_text
    )
    
    db.session.add(message)
    db.session.commit()
    
    # Emit real-time message to both participants
    message_data = message.to_dict()
    room_name = f'swap_{swap_id}'
    socketio.emit('new_message', message_data, room=room_name)
    
    return jsonify(message_data)

@socketio.on('join_swap_chat')
def handle_join_swap_chat(data):
    """Join a swap chat room"""
    swap_id = data.get('swap_id')
    if swap_id and current_user.is_authenticated:
        swap_request = SwapRequest.query.get(swap_id)
        if swap_request and (swap_request.requester_id == current_user.id or swap_request.receiver_id == current_user.id):
            room_name = f'swap_{swap_id}'
            socketio.join_room(room_name)

@socketio.on('leave_swap_chat')
def handle_leave_swap_chat(data):
    """Leave a swap chat room"""
    swap_id = data.get('swap_id')
    if swap_id and current_user.is_authenticated:
        room_name = f'swap_{swap_id}'
        socketio.leave_room(room_name)

 