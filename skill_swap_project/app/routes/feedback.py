from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..models import Feedback, SwapRequest, User
from .. import db

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/feedback/<int:swap_id>/add', methods=['POST'])
@login_required
def add_feedback(swap_id):
    """Add feedback for a completed swap"""
    swap_request = SwapRequest.query.get_or_404(swap_id)
    
    # Check if current user participated in this swap
    if swap_request.requester_id != current_user.id and swap_request.receiver_id != current_user.id:
        flash('You can only provide feedback for swaps you participated in', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    # Check if swap is completed
    if swap_request.status != 'completed':
        flash('You can only provide feedback for completed swaps', 'error')
        return redirect(url_for('swaps.my_swaps'))
    
    # Check if user already rated this swap
    existing_feedback = Feedback.query.filter_by(
        swap_id=swap_id,
        rater_id=current_user.id
    ).first()
    
    if existing_feedback:
        flash('You have already provided feedback for this swap', 'error')
        return redirect(url_for('swaps.view_swap', swap_id=swap_id))
    
    # Get form data
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    
    # Validation
    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating (1-5 stars)', 'error')
        return redirect(url_for('swaps.view_swap', swap_id=swap_id))
    
    # Determine the user being rated
    rated_user_id = swap_request.receiver_id if swap_request.requester_id == current_user.id else swap_request.requester_id
    
    # Create feedback
    feedback = Feedback(
        swap_id=swap_id,
        rater_id=current_user.id,
        rated_user_id=rated_user_id,
        rating=rating,
        comment=comment if comment else None
    )
    
    db.session.add(feedback)
    db.session.commit()
    
    flash('Feedback submitted successfully!', 'success')
    return redirect(url_for('swaps.view_swap', swap_id=swap_id))

@feedback_bp.route('/feedback/<int:feedback_id>/edit', methods=['POST'])
@login_required
def edit_feedback(feedback_id):
    """Edit existing feedback"""
    feedback = Feedback.query.get_or_404(feedback_id)
    
    # Check if current user owns this feedback
    if feedback.rater_id != current_user.id:
        flash('You can only edit your own feedback', 'error')
        return redirect(url_for('swaps.view_swap', swap_id=feedback.swap_id))
    
    # Get form data
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    
    # Validation
    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating (1-5 stars)', 'error')
        return redirect(url_for('swaps.view_swap', swap_id=feedback.swap_id))
    
    # Update feedback
    feedback.rating = rating
    feedback.comment = comment if comment else None
    
    db.session.commit()
    
    flash('Feedback updated successfully!', 'success')
    return redirect(url_for('swaps.view_swap', swap_id=feedback.swap_id))

@feedback_bp.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
@login_required
def delete_feedback(feedback_id):
    """Delete feedback"""
    feedback = Feedback.query.get_or_404(feedback_id)
    
    # Check if current user owns this feedback
    if feedback.rater_id != current_user.id:
        flash('You can only delete your own feedback', 'error')
        return redirect(url_for('swaps.view_swap', swap_id=feedback.swap_id))
    
    swap_id = feedback.swap_id
    
    db.session.delete(feedback)
    db.session.commit()
    
    flash('Feedback deleted successfully!', 'success')
    return redirect(url_for('swaps.view_swap', swap_id=swap_id))

@feedback_bp.route('/user/<int:user_id>/reviews')
def user_reviews(user_id):
    """View all reviews for a user"""
    user = User.query.get_or_404(user_id)
    
    if not user.is_public:
        flash('This profile is private', 'error')
        return redirect(url_for('users.search_users'))
    
    if user.is_banned:
        flash('This user has been banned', 'error')
        return redirect(url_for('users.search_users'))
    
    # Get all feedback for this user
    feedback_list = Feedback.get_user_feedback(user_id)
    
    # Get average rating and count
    avg_rating = Feedback.get_user_average_rating(user_id)
    rating_count = Feedback.get_user_rating_count(user_id)
    
    # Get rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        count = Feedback.query.filter_by(rated_user_id=user_id, rating=i).count()
        rating_distribution[i] = count
    
    return render_template('feedback/user_reviews.html',
                         user=user,
                         feedback_list=feedback_list,
                         avg_rating=avg_rating,
                         rating_count=rating_count,
                         rating_distribution=rating_distribution)

# API endpoints
@feedback_bp.route('/api/user/<int:user_id>/rating')
def get_user_rating(user_id):
    """Get user's average rating via API"""
    avg_rating = Feedback.get_user_average_rating(user_id)
    rating_count = Feedback.get_user_rating_count(user_id)
    
    return jsonify({
        'average_rating': avg_rating,
        'rating_count': rating_count
    })

@feedback_bp.route('/api/swap/<int:swap_id>/can-rate')
@login_required
def can_rate_swap(swap_id):
    """Check if user can rate a swap via API"""
    can_rate = Feedback.can_user_rate_swap(current_user.id, swap_id)
    return jsonify({'can_rate': can_rate})

@feedback_bp.route('/api/feedback/<int:feedback_id>')
def get_feedback(feedback_id):
    """Get specific feedback via API"""
    feedback = Feedback.query.get_or_404(feedback_id)
    return jsonify(feedback.to_dict()) 