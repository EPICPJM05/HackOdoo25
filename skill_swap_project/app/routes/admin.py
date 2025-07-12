from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from ..models import User, Admin, Skill, UserSkill, SwapRequest, Feedback
from .. import db
import csv
import io
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not hasattr(current_user, 'role'):
            flash('Admin access required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_banned=False).count()
    banned_users = User.query.filter_by(is_banned=True).count()
    
    total_swaps = SwapRequest.query.count()
    pending_swaps = SwapRequest.query.filter_by(status='pending').count()
    completed_swaps = SwapRequest.query.filter_by(status='completed').count()
    
    total_skills = Skill.query.count()
    approved_skills = Skill.query.filter_by(is_approved=True).count()
    pending_skills = Skill.query.filter_by(is_approved=False).count()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_swaps = SwapRequest.query.order_by(SwapRequest.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         banned_users=banned_users,
                         total_swaps=total_swaps,
                         pending_swaps=pending_swaps,
                         completed_swaps=completed_swaps,
                         total_skills=total_skills,
                         approved_skills=approved_skills,
                         pending_skills=pending_skills,
                         recent_users=recent_users,
                         recent_swaps=recent_swaps)

@admin_bp.route('/admin/users')
@admin_required
def manage_users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'all')
    
    query = User.query
    
    if search:
        query = query.filter(User.name.ilike(f'%{search}%') | User.email.ilike(f'%{search}%'))
    
    if status == 'active':
        query = query.filter_by(is_banned=False)
    elif status == 'banned':
        query = query.filter_by(is_banned=True)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/manage_users.html',
                         users=users,
                         search=search,
                         status=status)

@admin_bp.route('/admin/user/<int:user_id>/ban', methods=['POST'])
@admin_required
def ban_user(user_id):
    """Ban a user"""
    user = User.query.get_or_404(user_id)
    
    if user.is_banned:
        flash('User is already banned', 'info')
    else:
        user.is_banned = True
        db.session.commit()
        flash(f'User {user.name} has been banned', 'success')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/user/<int:user_id>/unban', methods=['POST'])
@admin_required
def unban_user(user_id):
    """Unban a user"""
    user = User.query.get_or_404(user_id)
    
    if not user.is_banned:
        flash('User is not banned', 'info')
    else:
        user.is_banned = False
        db.session.commit()
        flash(f'User {user.name} has been unbanned', 'success')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/skills')
@admin_required
def manage_skills():
    """Manage skills"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'all')
    
    query = Skill.query
    
    if search:
        query = query.filter(Skill.name.ilike(f'%{search}%'))
    
    if status == 'approved':
        query = query.filter_by(is_approved=True)
    elif status == 'pending':
        query = query.filter_by(is_approved=False)
    
    skills = query.order_by(Skill.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/manage_skills.html',
                         skills=skills,
                         search=search,
                         status=status)

@admin_bp.route('/admin/skill/<int:skill_id>/approve', methods=['POST'])
@admin_required
def approve_skill(skill_id):
    """Approve a skill"""
    skill = Skill.query.get_or_404(skill_id)
    
    if skill.is_approved:
        flash('Skill is already approved', 'info')
    else:
        skill.is_approved = True
        db.session.commit()
        flash(f'Skill {skill.name} has been approved', 'success')
    
    return redirect(url_for('admin.manage_skills'))

@admin_bp.route('/admin/skill/<int:skill_id>/reject', methods=['POST'])
@admin_required
def reject_skill(skill_id):
    """Reject a skill"""
    skill = Skill.query.get_or_404(skill_id)
    reason = request.form.get('reason', 'Inappropriate content')
    
    if not skill.is_approved:
        flash('Skill is already rejected', 'info')
    else:
        skill.is_approved = False
        skill.rejection_reason = reason
        db.session.commit()
        flash(f'Skill {skill.name} has been rejected: {reason}', 'success')
    
    return redirect(url_for('admin.manage_skills'))

@admin_bp.route('/admin/swaps')
@admin_required
def manage_swaps():
    """Manage swap requests"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    query = SwapRequest.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    swaps = query.order_by(SwapRequest.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/manage_swaps.html',
                         swaps=swaps,
                         status=status)

@admin_bp.route('/admin/messages')
@admin_required
def manage_messages():
    """Manage platform-wide messages"""
    return render_template('admin/manage_messages.html')

@admin_bp.route('/admin/messages/send', methods=['POST'])
@admin_required
def send_platform_message():
    """Send platform-wide message"""
    title = request.form.get('title', '').strip()
    message = request.form.get('message', '').strip()
    message_type = request.form.get('type', 'info')
    
    if not title or not message:
        flash('Title and message are required', 'error')
        return redirect(url_for('admin.manage_messages'))
    
    # Store the message in database (you can create a PlatformMessage model)
    # For now, we'll emit it via Socket.IO to all connected users
    
    # Emit to all connected users
    from .. import socketio
    socketio.emit('platform_message', {
        'title': title,
        'message': message,
        'type': message_type,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    flash(f'Platform message "{title}" sent successfully', 'success')
    return redirect(url_for('admin.manage_messages'))

@admin_bp.route('/admin/reports')
@admin_required
def reports():
    """Generate reports"""
    report_type = request.args.get('type', 'users')
    
    if report_type == 'users':
        data = generate_users_report()
        filename = f'users_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    elif report_type == 'swaps':
        data = generate_swaps_report()
        filename = f'swaps_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    elif report_type == 'feedback':
        data = generate_feedback_report()
        filename = f'feedback_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    elif report_type == 'activity':
        data = generate_activity_report()
        filename = f'activity_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    else:
        flash('Invalid report type', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return send_file(
        io.BytesIO(data.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@admin_bp.route('/admin/analytics')
@admin_required
def analytics():
    """View platform analytics"""
    # Get date range
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # User registration trends
    new_users = User.query.filter(
        User.created_at >= start_date
    ).count()
    
    # Swap activity trends
    new_swaps = SwapRequest.query.filter(
        SwapRequest.created_at >= start_date
    ).count()
    
    completed_swaps = SwapRequest.query.filter(
        SwapRequest.completed_at >= start_date
    ).count()
    
    # Top skills
    from sqlalchemy import func
    top_skills = db.session.query(
        UserSkill.skill_name,
        func.count(UserSkill.id).label('count')
    ).filter(
        UserSkill.created_at >= start_date
    ).group_by(UserSkill.skill_name).order_by(
        func.count(UserSkill.id).desc()
    ).limit(10).all()
    
    return render_template('admin/analytics.html',
                         days=days,
                         new_users=new_users,
                         new_swaps=new_swaps,
                         completed_swaps=completed_swaps,
                         top_skills=top_skills)

def generate_users_report():
    """Generate users report"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Name', 'Email', 'Location', 'Status', 'Created At', 'Total Swaps', 'Avg Rating'])
    
    # Get all users with their stats
    users = User.query.all()
    for user in users:
        total_swaps = SwapRequest.query.filter(
            (SwapRequest.requester_id == user.id) | (SwapRequest.receiver_id == user.id)
        ).count()
        
        avg_rating = Feedback.get_user_average_rating(user.id)
        
        status = 'Banned' if user.is_banned else 'Active'
        
        writer.writerow([
            user.id,
            user.name,
            user.email,
            user.location or '',
            status,
            user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
            total_swaps,
            avg_rating
        ])
    
    return output.getvalue()

def generate_swaps_report():
    """Generate swaps report"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Requester', 'Receiver', 'Requester Skill', 'Receiver Skill', 'Status', 'Created At', 'Completed At'])
    
    # Get all swaps
    swaps = SwapRequest.query.all()
    for swap in swaps:
        requester = User.query.get(swap.requester_id)
        receiver = User.query.get(swap.receiver_id)
        
        writer.writerow([
            swap.id,
            requester.name if requester else 'Unknown',
            receiver.name if receiver else 'Unknown',
            swap.requester_skill,
            swap.receiver_skill,
            swap.status,
            swap.created_at.strftime('%Y-%m-%d %H:%M:%S') if swap.created_at else '',
            swap.completed_at.strftime('%Y-%m-%d %H:%M:%S') if swap.completed_at else ''
        ])
    
    return output.getvalue()

def generate_feedback_report():
    """Generate feedback report"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Swap ID', 'Rater', 'Rated User', 'Rating', 'Comment', 'Created At'])
    
    # Get all feedback
    feedback_list = Feedback.query.all()
    for feedback in feedback_list:
        rater = User.query.get(feedback.rater_id)
        rated_user = User.query.get(feedback.rated_user_id)
        
        writer.writerow([
            feedback.id,
            feedback.swap_id,
            rater.name if rater else 'Unknown',
            rated_user.name if rated_user else 'Unknown',
            feedback.rating,
            feedback.comment or '',
            feedback.created_at.strftime('%Y-%m-%d %H:%M:%S') if feedback.created_at else ''
        ])
    
    return output.getvalue()

def generate_activity_report():
    """Generate user activity report"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['User ID', 'User Name', 'Email', 'Registration Date', 'Last Login', 'Total Skills', 'Total Swaps', 'Completed Swaps', 'Avg Rating', 'Status'])
    
    # Get all users with their activity stats
    users = User.query.all()
    for user in users:
        # Count user's skills
        total_skills = UserSkill.query.filter_by(user_id=user.id).count()
        
        # Count user's swaps
        total_swaps = SwapRequest.query.filter(
            (SwapRequest.requester_id == user.id) | (SwapRequest.receiver_id == user.id)
        ).count()
        
        # Count completed swaps
        completed_swaps = SwapRequest.query.filter(
            ((SwapRequest.requester_id == user.id) | (SwapRequest.receiver_id == user.id)) &
            (SwapRequest.status == 'completed')
        ).count()
        
        # Get average rating
        avg_rating = Feedback.get_user_average_rating(user.id)
        
        # Determine status
        status = 'Banned' if user.is_banned else 'Active'
        
        writer.writerow([
            user.id,
            user.name,
            user.email,
            user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
            user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else '',
            total_skills,
            total_swaps,
            completed_swaps,
            avg_rating,
            status
        ])
    
    return output.getvalue()

# API endpoints for admin dashboard
@admin_bp.route('/api/admin/stats')
@admin_required
def get_admin_stats():
    """Get admin dashboard statistics"""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_banned=False).count()
    total_swaps = SwapRequest.query.count()
    pending_swaps = SwapRequest.query.filter_by(status='pending').count()
    completed_swaps = SwapRequest.query.filter_by(status='completed').count()
    
    # Get recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= week_ago).count()
    new_swaps_week = SwapRequest.query.filter(SwapRequest.created_at >= week_ago).count()
    
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'total_swaps': total_swaps,
        'pending_swaps': pending_swaps,
        'completed_swaps': completed_swaps,
        'new_users_week': new_users_week,
        'new_swaps_week': new_swaps_week
    }) 