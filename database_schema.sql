-- =====================================================
-- Skill Swap Platform - Complete Database Schema
-- =====================================================

-- Create database
CREATE DATABASE IF NOT EXISTS skill_swap;
USE skill_swap;

-- =====================================================
-- 1. USERS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    location VARCHAR(100),
    photo_url VARCHAR(255),
    availability VARCHAR(100),
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. SKILLS OFFERED TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS skills_offered (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =====================================================
-- 3. SKILLS WANTED TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS skills_wanted (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =====================================================
-- 4. SWAP REQUESTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS swap_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    requester_id INT NOT NULL,
    receiver_id INT NOT NULL,
    status ENUM('pending', 'accepted', 'rejected', 'completed') DEFAULT 'pending',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =====================================================
-- 5. FEEDBACK TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    swap_id INT NOT NULL,
    rater_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (swap_id) REFERENCES swap_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (rater_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =====================================================
-- 6. ADMINS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INSERT DEFAULT ADMIN USER
-- =====================================================
-- Password: admin123 (hashed with Werkzeug)
INSERT IGNORE INTO admins (email, password) VALUES 
('admin@skillswap.com', 'pbkdf2:sha256:600000$YOUR_HASH_HERE');

-- =====================================================
-- 7. MESSAGES TABLE (for chat)
-- =====================================================
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    swap_id INT NOT NULL,
    sender_id INT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (swap_id) REFERENCES swap_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =====================================================
-- SAMPLE DATA FOR TESTING (Optional)
-- =====================================================

-- Sample Users
INSERT INTO users (name, email, password, location, availability, is_public) VALUES
('John Doe', 'john@example.com', 'pbkdf2:sha256:600000$sample_hash_1', 'New York, USA', 'Weekends', TRUE),
('Jane Smith', 'jane@example.com', 'pbkdf2:sha256:600000$sample_hash_2', 'London, UK', 'Evenings', TRUE),
('Mike Johnson', 'mike@example.com', 'pbkdf2:sha256:600000$sample_hash_3', 'Toronto, Canada', 'Flexible', TRUE),
('Sarah Wilson', 'sarah@example.com', 'pbkdf2:sha256:600000$sample_hash_4', 'Sydney, Australia', 'Weekdays', TRUE);

-- Sample Skills Offered
INSERT INTO skills_offered (user_id, skill_name, description) VALUES
(1, 'Python Programming', 'Expert in Python with 5+ years experience. Can teach web development, data analysis, and automation.'),
(1, 'Guitar', 'Classical and acoustic guitar. 10+ years of playing experience.'),
(2, 'Spanish Language', 'Native Spanish speaker. Can teach conversational Spanish and grammar.'),
(2, 'Photography', 'Professional photographer specializing in portrait and landscape photography.'),
(3, 'Cooking', 'Chef with experience in Italian, French, and Asian cuisines.'),
(3, 'Excel', 'Advanced Excel user. Can teach formulas, pivot tables, and data analysis.'),
(4, 'Yoga', 'Certified yoga instructor. Specializes in Vinyasa and Hatha yoga.'),
(4, 'JavaScript', 'Frontend developer with expertise in React, Vue, and vanilla JavaScript.');

-- Sample Skills Wanted
INSERT INTO skills_wanted (user_id, skill_name, description) VALUES
(1, 'Spanish Language', 'Want to learn conversational Spanish for travel.'),
(1, 'Photography', 'Interested in learning basic photography techniques.'),
(2, 'Python Programming', 'Want to learn Python for data analysis.'),
(2, 'Cooking', 'Looking to learn basic cooking skills.'),
(3, 'Guitar', 'Complete beginner wanting to learn acoustic guitar.'),
(3, 'Yoga', 'Want to learn yoga for fitness and relaxation.'),
(4, 'Excel', 'Need to improve Excel skills for work.'),
(4, 'JavaScript', 'Want to learn JavaScript for web development.');

-- Sample Swap Requests
INSERT INTO swap_requests (requester_id, receiver_id, status, timestamp) VALUES
(1, 2, 'pending', NOW() - INTERVAL 2 DAY),
(2, 3, 'accepted', NOW() - INTERVAL 1 DAY),
(3, 4, 'completed', NOW() - INTERVAL 5 DAY),
(4, 1, 'rejected', NOW() - INTERVAL 3 DAY);

-- Sample Feedback
INSERT INTO feedback (swap_id, rater_id, rating, comment) VALUES
(3, 3, 5, 'Excellent teaching! Very patient and knowledgeable.'),
(3, 4, 4, 'Great learning experience. Would recommend!');

-- =====================================================
-- USEFUL QUERIES FOR TESTING
-- =====================================================

-- View all users with their skills
SELECT 
    u.name,
    u.email,
    u.location,
    u.availability,
    GROUP_CONCAT(DISTINCT so.skill_name) as skills_offered,
    GROUP_CONCAT(DISTINCT sw.skill_name) as skills_wanted
FROM users u
LEFT JOIN skills_offered so ON u.id = so.user_id
LEFT JOIN skills_wanted sw ON u.id = sw.user_id
WHERE u.is_public = 1
GROUP BY u.id;

-- View swap requests with user details
SELECT 
    sr.id,
    sr.status,
    sr.timestamp,
    u1.name as requester_name,
    u2.name as receiver_name
FROM swap_requests sr
JOIN users u1 ON sr.requester_id = u1.id
JOIN users u2 ON sr.receiver_id = u2.id
ORDER BY sr.timestamp DESC;

-- View user ratings
SELECT 
    u.name,
    AVG(f.rating) as avg_rating,
    COUNT(f.rating) as total_ratings
FROM users u
LEFT JOIN swap_requests sr ON (u.id = sr.requester_id OR u.id = sr.receiver_id)
LEFT JOIN feedback f ON sr.id = f.swap_id
WHERE sr.status = 'completed'
GROUP BY u.id;

-- Search users by skill
SELECT 
    u.name,
    u.location,
    u.availability,
    so.skill_name,
    so.description
FROM users u
JOIN skills_offered so ON u.id = so.user_id
WHERE u.is_public = 1 
AND so.skill_name LIKE '%Python%';

-- =====================================================
-- INDEXES FOR BETTER PERFORMANCE
-- =====================================================

-- Index on email for faster login
CREATE INDEX idx_users_email ON users(email);

-- Index on skill names for faster search
CREATE INDEX idx_skills_offered_name ON skills_offered(skill_name);
CREATE INDEX idx_skills_wanted_name ON skills_wanted(skill_name);

-- Index on swap request status and timestamps
CREATE INDEX idx_swap_requests_status ON swap_requests(status);
CREATE INDEX idx_swap_requests_timestamp ON swap_requests(timestamp);

-- Index on user_id for faster joins
CREATE INDEX idx_skills_offered_user ON skills_offered(user_id);
CREATE INDEX idx_skills_wanted_user ON skills_wanted(user_id);
CREATE INDEX idx_swap_requests_requester ON swap_requests(requester_id);
CREATE INDEX idx_swap_requests_receiver ON swap_requests(receiver_id);

-- =====================================================
-- DATABASE COMPLETED
-- =====================================================

-- Show all tables
SHOW TABLES;

-- Show table structures
DESCRIBE users;
DESCRIBE skills_offered;
DESCRIBE skills_wanted;
DESCRIBE swap_requests;
DESCRIBE feedback;
DESCRIBE admins; 