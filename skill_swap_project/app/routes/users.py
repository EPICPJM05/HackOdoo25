from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from ..models import User, UserSkill, Skill, Availability, Feedback
from .. import db
from ..utils.validators import validate_skill_name

users_bp = Blueprint('users', __name__)

def allowed_file(filename):
    """Check if uploaded file is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@users_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    # Get user's skills
    offered_skills = UserSkill.get_user_offered_skills(current_user.id)
    wanted_skills = UserSkill.get_user_wanted_skills(current_user.id)
    
    # Get user's availability
    availability = Availability.get_user_availability(current_user.id)
    
    # Get user's average rating
    avg_rating = Feedback.get_user_average_rating(current_user.id)
    rating_count = Feedback.get_user_rating_count(current_user.id)
    
    # Get recent swap requests
    from ..models import SwapRequest
    recent_swaps = SwapRequest.get_user_requests(current_user.id)[:5]
    
    return render_template('users/profile.html',
                         offered_skills=offered_skills,
                         wanted_skills=wanted_skills,
                         availability=availability,
                         avg_rating=avg_rating,
                         rating_count=rating_count,
                         recent_swaps=recent_swaps)

@users_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        availability = request.form.get('availability', 'weekends')
        is_public = request.form.get('is_public') == 'on'
        
        # Handle photo upload
        photo_url = current_user.photo_url
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"user_{current_user.id}_{file.filename}")
                filepath = os.path.join('static', 'uploads', filename)
                full_path = os.path.join(current_app.root_path, filepath)
                file.save(full_path)
                photo_url = f"/static/uploads/{filename}"
        
        # Validation
        if not name:
            flash('Name is required', 'error')
            return render_template('users/edit_profile.html')
        
        if len(name) < 2:
            flash('Name must be at least 2 characters long', 'error')
            return render_template('users/edit_profile.html')
        
        # Update user
        current_user.name = name
        current_user.location = location if location else None
        current_user.availability = availability
        current_user.is_public = is_public
        current_user.photo_url = photo_url
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('users.profile'))
    
    return render_template('users/edit_profile.html')

@users_bp.route('/skills/add', methods=['POST'])
@login_required
def add_skill():
    """Add a skill to user's profile"""
    skill_name = request.form.get('skill_name', '').strip()
    skill_type = request.form.get('skill_type', 'offered')
    description = request.form.get('description', '').strip()
    proficiency_level = request.form.get('proficiency_level', 'intermediate')
    
    if not skill_name:
        flash('Skill name is required', 'error')
        return redirect(url_for('users.profile'))
    
    if skill_type not in ['offered', 'wanted']:
        flash('Invalid skill type', 'error')
        return redirect(url_for('users.profile'))
    
    # Find or create the skill
    from ..models.skill import Skill
    skill = Skill.query.filter_by(name=skill_name).first()
    if not skill:
        # Create new skill
        skill = Skill(name=skill_name, description=description)
        db.session.add(skill)
        db.session.flush()  # Get the ID without committing
    
    # Check if skill already exists for this user
    existing_skill = UserSkill.query.filter_by(
        user_id=current_user.id,
        skill_id=skill.id,
        skill_type=skill_type
    ).first()
    
    if existing_skill:
        flash(f'You already have {skill_name} in your {skill_type} skills', 'error')
        return redirect(url_for('users.profile'))
    
    # Create new user skill
    user_skill = UserSkill(
        user_id=current_user.id,
        skill_id=skill.id,
        skill_name=skill_name,
        skill_type=skill_type,
        description=description if description else None,
        proficiency_level=proficiency_level
    )
    
    db.session.add(user_skill)
    db.session.commit()
    
    flash(f'{skill_name} added to your {skill_type} skills!', 'success')
    return redirect(url_for('users.profile'))

@users_bp.route('/skills/<int:skill_id>/edit', methods=['POST'])
@login_required
def edit_skill(skill_id):
    """Edit a user skill"""
    user_skill = UserSkill.query.get_or_404(skill_id)
    
    # Check ownership
    if user_skill.user_id != current_user.id:
        flash('You can only edit your own skills', 'error')
        return redirect(url_for('users.profile'))
    
    description = request.form.get('description', '').strip()
    proficiency_level = request.form.get('proficiency_level', 'intermediate')
    
    user_skill.description = description if description else None
    user_skill.proficiency_level = proficiency_level
    
    db.session.commit()
    flash('Skill updated successfully!', 'success')
    return redirect(url_for('users.profile'))

@users_bp.route('/skills/<int:skill_id>/delete', methods=['POST'])
@login_required
def delete_skill(skill_id):
    """Delete a user skill"""
    user_skill = UserSkill.query.get_or_404(skill_id)
    
    # Check ownership
    if user_skill.user_id != current_user.id:
        flash('You can only delete your own skills', 'error')
        return redirect(url_for('users.profile'))
    
    skill_name = user_skill.skill_name
    skill_type = user_skill.skill_type
    
    db.session.delete(user_skill)
    db.session.commit()
    
    flash(f'{skill_name} removed from your {skill_type} skills!', 'success')
    return redirect(url_for('users.profile'))

@users_bp.route('/search')
def search_users():
    """Search users by skill"""
    skill_name = request.args.get('skill', '').strip()
    skill_type = request.args.get('type', 'offered')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    if not skill_name:
        # Show all public users
        users = User.query.filter_by(is_public=True, is_banned=False)\
                         .paginate(page=page, per_page=per_page, error_out=False)
        return render_template('users/search.html', users=users, skill_name='', skill_type='')
    
    # Search users by skill
    user_skills = UserSkill.query.filter_by(
        skill_name=skill_name,
        skill_type=skill_type
    ).all()
    
    user_ids = [us.user_id for us in user_skills]
    users = User.query.filter(
        User.id.in_(user_ids),
        User.is_public == True,
        User.is_banned == False
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('users/search.html', 
                         users=users, 
                         skill_name=skill_name, 
                         skill_type=skill_type)

@users_bp.route('/user/<int:user_id>')
def view_user(user_id):
    """View another user's profile"""
    user = User.query.get_or_404(user_id)
    
    if not user.is_public:
        flash('This profile is private', 'error')
        return redirect(url_for('users.search_users'))
    
    if user.is_banned:
        flash('This user has been banned', 'error')
        return redirect(url_for('users.search_users'))
    
    # Get user's skills
    offered_skills = UserSkill.get_user_offered_skills(user.id)
    wanted_skills = UserSkill.get_user_wanted_skills(user.id)
    
    # Get user's average rating
    avg_rating = Feedback.get_user_average_rating(user.id)
    rating_count = Feedback.get_user_rating_count(user.id)
    
    # Check if current user can send swap request
    can_send_request = False
    current_user_offered_skills = []
    
    if current_user.is_authenticated and current_user.id != user.id:
        # Get current user's offered skills for swap request form
        current_user_offered_skills = UserSkill.get_user_offered_skills(current_user.id)
        
        # Check if user is available for swaps
        can_send_request = user.is_available_for_swaps()
        
        # Check if there's already a pending request
        from ..models import SwapRequest
        existing_request = SwapRequest.query.filter_by(
            requester_id=current_user.id,
            receiver_id=user.id,
            status='pending'
        ).first()
        if existing_request:
            can_send_request = False
    
    return render_template('users/view_user.html',
                         user=user,
                         offered_skills=offered_skills,
                         wanted_skills=wanted_skills,
                         avg_rating=avg_rating,
                         rating_count=rating_count,
                         can_send_request=can_send_request,
                         current_user_offered_skills=current_user_offered_skills)

# API endpoints
@users_bp.route('/api/skills/search', methods=['POST'])
def search_skills():
    """Search skills via API"""
    data = request.get_json()
    search_term = data.get('search', '').strip()
    
    if not search_term:
        return jsonify({'skills': []})
    
    skills = Skill.search_by_name(search_term)
    return jsonify({'skills': [skill.name for skill in skills]})

@users_bp.route('/api/users/<int:user_id>/skills')
def get_user_skills(user_id):
    """Get user skills via API"""
    user = User.query.get_or_404(user_id)
    
    offered_skills = UserSkill.get_user_offered_skills(user.id)
    wanted_skills = UserSkill.get_user_wanted_skills(user.id)
    
    return jsonify({
        'offered': [skill.skill_name for skill in offered_skills],
        'wanted': [skill.skill_name for skill in wanted_skills]
    })

@users_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account"""
    # Get all related data to delete
    from ..models import SwapRequest, Feedback, UserSkill
    
    # Delete swap requests
    SwapRequest.query.filter_by(requester_id=current_user.id).delete()
    SwapRequest.query.filter_by(receiver_id=current_user.id).delete()
    
    # Delete feedback
    Feedback.query.filter_by(reviewer_id=current_user.id).delete()
    Feedback.query.filter_by(reviewed_user_id=current_user.id).delete()
    
    # Delete user skills
    UserSkill.query.filter_by(user_id=current_user.id).delete()
    
    # Delete the user
    db.session.delete(current_user)
    db.session.commit()
    
    flash('Your account has been deleted successfully.', 'success')
    return redirect(url_for('auth.login')) 