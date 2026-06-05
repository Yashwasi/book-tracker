from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a real secret key

# 📦 Initialize database and tables
def init_db():
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()

    # 📚 Updated Book table (correct column names!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT NOT NULL,
            description TEXT,
            genre TEXT,
            user_email TEXT,
            review TEXT,
            thumbnail TEXT
        )
    ''')

    # 👤 User table remains the same
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

 


# 🏠 Home page
@app.route('/')
def home():
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute("SELECT title, authors, review FROM books")
    books = [dict(title=row[0], authors=row[1], review=row[2]) for row in cursor.fetchall()]
    conn.close()
    return render_template('home.html', books=books)


# 📚 Bookshelf page (only user’s books)
@app.route('/bookshelf')
def bookshelf():
    if 'user_email' not in session:
        flash("Please log in to view your bookshelf.")
        return redirect("/login")

    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()

    # ✅ Updated: using 'authors' column now
    cursor.execute("SELECT id, title, authors, description, genre, thumbnail FROM books WHERE user_email = ?", (session['user_email'],))
    books = [
        {
            'id': row[0],
            'title': row[1],
            'author': row[2],  # coming from 'authors' column
            'description': row[3],
            'genre': row[4],
            'thumbnail': row[5]
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return render_template("mybooks.html", books=books)

@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    user_email = session.get('user_email')

    if not user_email:
        flash("Please login first.", "error")
        return redirect(url_for('login'))

    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM books WHERE id = ? AND user_email = ?", (book_id, user_email))
    conn.commit()
    conn.close()

    flash("❌ Book deleted from your bookshelf.", "success")
    return redirect(url_for('bookshelf'))

@app.route('/edit/<int:book_id>', methods=['GET'])
def edit_book(book_id):
    user_email = session.get('user_email')
    if not user_email:
        flash("Please log in to edit your books.", "warning")
        return redirect(url_for('login'))

    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row  # 👈 So we can access columns by name
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM books WHERE id = ? AND user_email = ?", (book_id, user_email))
    book = cursor.fetchone()

    conn.close()

    if not book:
        flash("Book not found.", "error")
        return redirect(url_for('bookshelf'))

    return render_template('edit_book.html', book=book)




@app.route('/update/<int:book_id>', methods=['POST'])
def update_book(book_id):
    title = request.form.get('title')
    authors = request.form.get('authors')
    description = request.form.get('description')
    genre = request.form.get('genre')
    user_email = session.get('user_email')
    notes = request.form.get('notes')
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()

    try:
        cursor.execute("""
    UPDATE books
    SET title = ?, authors = ?, description = ?, genre = ?, notes = ?
    WHERE id = ? AND user_email = ?
    """, (title, authors, description, genre, notes, book_id, user_email))
        conn.commit()
        flash("✅ Book updated successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(url_for('bookshelf'))


@app.route('/recommendation')
def recommendation():
    if 'user_email' not in session:
        flash("Please login to see recommendations.")
        return redirect(url_for('login'))

    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()

    # Fetch genres or authors from user's bookshelf
    cursor.execute("SELECT title, authors, genre FROM books WHERE user_email = ?", (session['user_email'],))
    user_books = cursor.fetchall()
    conn.close()

    # Extract genres or authors
    genres = list(set([book[2] for book in user_books if book[2] and book[2] != "Not specified"]))
    authors = list(set([book[1] for book in user_books if book[1]]))

    # Basic logic: Recommend some preset books based on genres/authors
    recommended_books = []

    if 'Fantasy' in genres:
        recommended_books.append({
            'title': 'The Night Circus',
            'author': 'Erin Morgenstern',
            'description': 'A magical tale of a mysterious circus and two star-crossed magicians.',
            'thumbnail': 'https://i.imgur.com/D8JQ2V7.jpg'
        })

    if 'Sci-Fi' in genres:
        recommended_books.append({
            'title': 'Dune',
            'author': 'Frank Herbert',
            'description': 'A science fiction classic set in a desert world of political intrigue and prophecy.',
            'thumbnail': 'https://i.imgur.com/GRn6W1K.jpg'
        })

    if not recommended_books:
        recommended_books.append({
            'title': 'Pride and Prejudice',
            'author': 'Jane Austen',
            'description': 'When in doubt, always recommend a classic.',
            'thumbnail': 'https://i.imgur.com/g1WaiXv.jpg'
        })

    return render_template('recommendation.html', books=recommended_books)

import requests

#SEARCH PAGE
@app.route('/search')
def search_page():
    return render_template('search.html')  # search form page

#RESULT PAGE
@app.route('/search/results')
def search_results():
    query = request.args.get('query')
    results = []

    if query:
        response = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": query})
        if response.status_code == 200:
            data = response.json()

            print("STATUS:", response.status_code)
            print("ITEMS FOUND:", len(data.get('items', [])))

            for item in data.get('items', []):
                volume_info = item['volumeInfo']
                results.append({
                    'title': volume_info.get('title', 'N/A'),
                    'authors': ', '.join(volume_info.get('authors', ['Unknown'])),
                    'description': volume_info.get('description', 'No description available.'),
                    'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', '')
                })

    return render_template('results.html', books=results, query=query)


@app.route('/add', methods=['POST'])
def add_book():
    # ✅ Check if user is logged in
    if 'user_email' not in session:
        flash("🔐 Please log in to add books to your bookshelf.", "warning")
        return redirect(url_for('login'))

    title = request.form.get('title')
    authors = request.form.get('authors')
    description = request.form.get('description')
    thumbnail = request.form.get('thumbnail')
    genre = request.form.get('genre', 'Not specified')
    user_email = session.get('user_email')  # already safe now

    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM books WHERE title = ? AND user_email = ?", (title, user_email))
        existing = cursor.fetchone()

        if not existing:
            cursor.execute("""
                INSERT INTO books (title, authors, description, genre, user_email, thumbnail)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, authors, description, genre, user_email, thumbnail))
            conn.commit()
            flash("📚 Book added to your bookshelf!", "success")
        else:
            flash("⚠️ Book already exists in your bookshelf.", "warning")

    except Exception as e:
        flash("⚠️ Something went wrong while adding the book. Please try again.", "error")
        # ❌ Avoid showing technical errors like str(e)

    finally:
        conn.close()

    return redirect(url_for('bookshelf'))


def get_book_by_id(book_id):
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, authors, description, genre, thumbnail FROM books WHERE id = ?", (book_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'title': row[1],
            'authors': row[2],
            'description': row[3],
            'genre': row[4],
            'thumbnail': row[5]
        }
    return None

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = get_book_by_id(book_id)  # Replace this with your actual DB logic
    if not book:
        return "Book not found", 404
    return render_template('book_detail.html', book=book)

@app.route('/about')
def about():
    return render_template('about.html')



# 📝 Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        if not name or not email or not password:
            flash("Please fill in all the fields.")
            return redirect("/signup")

        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("This email is already registered. Please login.")
            conn.close()
            return redirect("/signup")

        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                       (name, email, hashed_password))
        conn.commit()
        conn.close()

        # Store session
        session['user_name'] = name
        session['user_email'] = email

        flash("Account created successfully! 🎉")
        return redirect("/")

    return render_template('signup.html')


# 🔐 Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()

        conn = sqlite3.connect("books.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_name'] = user[0]
            session['user_email'] = email
            flash("Logged in successfully! 🎉")
            return redirect("/")
        else:
            flash("Invalid email or password.")
            return redirect("/login")

    return render_template("login.html")


# 🚪 Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect("/")


import os

if __name__ == '__main__':
    init_db()
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    ) 