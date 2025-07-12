import mysql.connector
from mysql.connector import Error

def create_database():
    """Create the skill_swap database and all required tables"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS skill_swap")
            cursor.execute("USE skill_swap")
            
            # Create users table
            cursor.execute("""
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
                )
            """)
            
            # Create skills_offered table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills_offered (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    skill_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create skills_wanted table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills_wanted (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    skill_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create swap_requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS swap_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    requester_id INT NOT NULL,
                    receiver_id INT NOT NULL,
                    status ENUM('pending', 'accepted', 'rejected', 'completed') DEFAULT 'pending',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    swap_id INT NOT NULL,
                    rater_id INT NOT NULL,
                    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (swap_id) REFERENCES swap_requests(id) ON DELETE CASCADE,
                    FOREIGN KEY (rater_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create admins table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default admin user
            from werkzeug.security import generate_password_hash
            admin_password = generate_password_hash('admin123')
            cursor.execute("""
                INSERT IGNORE INTO admins (email, password) VALUES (%s, %s)
            """, ('admin@skillswap.com', admin_password))
            
            connection.commit()
            print("Database and tables created successfully!")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='skill_swap'
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

if __name__ == "__main__":
    create_database() 