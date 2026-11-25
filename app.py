import os
from datetime import datetime
import streamlit as st

BOOKS_FILE = "books.txt"
STUDENTS_FILE = "students.txt"
RECORDS_FILE = "records.txt"

st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide"
)


def clean(value):
    return str(value).replace(",", " ").strip()


def current_time():
    return datetime.now().astimezone().strftime("%d-%m-%Y %I:%M:%S %p")


def load_file(filename, expected_columns):
    data = []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line:
                    continue

                row = [item.strip() for item in line.split(",")]

                # Support old 3-column records and new 5-column records
                if filename == RECORDS_FILE and len(row) == 3:
                    row.extend(["", ""])

                if len(row) != expected_columns or any(
                    not item for item in row[:3]):
                    raise ValueError(
                        f"Invalid data in {filename}, line {line_number}"
                    )

                data.append(row)

    except FileNotFoundError:
        return []

    return data


def save_file(filename, data):
    temp_file = filename + ".tmp"

    try:
        with open(temp_file, "w", encoding="utf-8") as file:
            for row in data:
                file.write(",".join(row) + "\n")

        os.replace(temp_file, filename)

    except OSError:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise


def initialize():
    if "books" not in st.session_state:
        st.session_state.books = load_file(BOOKS_FILE, 4)

        for book in st.session_state.books:
            if not book[3].isdecimal():
                raise ValueError("Invalid copies value in books.txt")

            book[3] = str(int(book[3]))

    if "students" not in st.session_state:
        st.session_state.students = load_file(STUDENTS_FILE, 2)

    if "records" not in st.session_state:
        st.session_state.records = load_file(RECORDS_FILE, 5)

        if any(
            r[2] not in ("Issued", "Returned")
            for r in st.session_state.records
        ):
            raise ValueError("Invalid record status in records.txt")


try:
    initialize()

except (ValueError, OSError) as error:
    st.error(f"Unable to load library data: {error}")
    st.stop()


books = st.session_state.books
students = st.session_state.students
records = st.session_state.records

# Ensure old records also support timestamp fields
for record in records:
    while len(record) < 5:
        record.append("")


def find_book(book_id):
    return next((b for b in books if b[0] == book_id), None)


def find_student(roll):
    return next((s for s in students if s[0] == roll), None)


def active_issue_exists(roll, book_id):
    return any(
        r[0] == roll and r[1] == book_id and r[2] == "Issued"
        for r in records
    )


# -------------------- STYLING --------------------

st.markdown("""
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    .hero {
        padding: 1.5rem 1.7rem;
        border-radius: 18px;
        background: linear-gradient(
            120deg, #172554, #1e3a8a, #0f766e
        );
        color: white;
        margin-bottom: 1.3rem;
    }

    .hero h1 {
        color: white;
        margin: 0;
        font-size: 2.1rem;
    }

    .hero p {
        color: #dbeafe;
        margin: .45rem 0 0 0;
    }

    div[data-testid="stMetric"] {
        background: #3B2F2F !important;
        padding: 14px;
        border: 1px solid #66514A;
        border-radius: 12px;
    }

    div[data-testid="stMetricLabel"] {
        color: #E6D5C3 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }

    .small-note {
        color: #64748b;
        font-size: .9rem;
    }
</style>
""", unsafe_allow_html=True)


# -------------------- HEADER --------------------

st.markdown("""
<div class="hero">
  <h1>📚 Library Management System</h1>
  <p>Manage books, student registrations and borrowing records in one place.</p>
</div>
""", unsafe_allow_html=True)


# -------------------- DASHBOARD METRICS --------------------

active_count = sum(1 for r in records if r[2] == "Issued")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total book titles", len(books))
c2.metric("Registered students", len(students))
c3.metric("Active issues", active_count)
c4.metric("Available copies", sum(int(b[3]) for b in books))


# -------------------- NAVIGATION --------------------

menu = st.sidebar.radio("NAVIGATION", [
    "Dashboard",
    "Add Book",
    "View Books",
    "Register Student",
    "View Students",
    "Issue Book",
    "Return Book",
    "View Records"
])

st.sidebar.markdown("---")
st.sidebar.caption("Python • Functions • Lists • Text-file storage")
st.sidebar.caption("Academic Project Demo")


# -------------------- DASHBOARD --------------------

if menu == "Dashboard":

    st.subheader("Dashboard")

    left, right = st.columns(2)

    with left:
        st.markdown("#### Recent borrowing records")

        if records:
            recent = []

            for r in records[-8:][::-1]:
                recent.append({
                    "Roll No": r[0],
                    "Book ID": r[1],
                    "Status": r[2],
                    "Issue Time": r[3] or "Not recorded",
                    "Return Time": r[4] or "Not returned"
                })

            st.dataframe(
                recent,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No borrowing records yet. Issue a book to get started.")

    with right:
        st.markdown("#### Available books")

        if books:
            st.dataframe(
                [
                    {
                        "Book ID": b[0],
                        "Title": b[1],
                        "Author": b[2],
                        "Copies": int(b[3])
                    }
                    for b in books
                ],
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No books added yet. Use Add Book to create the first record.")

    st.caption(
        "Note: This is a browser-based demonstration interface "
        "for the submitted menu-driven Python project."
    )


# -------------------- ADD BOOK --------------------

elif menu == "Add Book":

    st.subheader("Add a Book")

    with st.form("add_book_form", clear_on_submit=True):

        book_id = st.text_input("Book ID")
        title = st.text_input("Title")
        author = st.text_input("Author")
        copies = st.number_input(
            "Number of copies",
            min_value=1,
            step=1,
            value=1
        )

        submitted = st.form_submit_button(
            "Add Book",
            type="primary"
        )

    if submitted:

        book_id = clean(book_id)
        title = clean(title)
        author = clean(author)

        if not all([book_id, title, author]):
            st.error("All fields are required.")

        elif find_book(book_id):
            st.error("A book with this ID already exists.")

        else:
            books.append([
                book_id,
                title,
                author,
                str(int(copies))
            ])

            save_file(BOOKS_FILE, books)

            st.success("Book added successfully!")


# -------------------- VIEW BOOKS --------------------

elif menu == "View Books":

    st.subheader("Book Catalogue")

    if books:

        st.dataframe(
            [
                {
                    "Book ID": b[0],
                    "Title": b[1],
                    "Author": b[2],
                    "Available Copies": int(b[3])
                }
                for b in books
            ],
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No books available.")


# -------------------- REGISTER STUDENT --------------------

elif menu == "Register Student":

    st.subheader("Register a Student")

    with st.form("register_student_form", clear_on_submit=True):

        roll = st.text_input("Roll Number")
        name = st.text_input("Student Name")

        submitted = st.form_submit_button(
            "Register Student",
            type="primary"
        )

    if submitted:

        roll = clean(roll)
        name = clean(name)

        if not roll or not name:
            st.error("All fields are required.")

        elif find_student(roll):
            st.error("This student is already registered.")

        else:
            students.append([roll, name])

            save_file(STUDENTS_FILE, students)

            st.success("Student registered successfully!")


# -------------------- VIEW STUDENTS --------------------

elif menu == "View Students":

    st.subheader("Registered Students")

    if students:

        st.dataframe(
            [
                {
                    "Roll Number": s[0],
                    "Name": s[1]
                }
                for s in students
            ],
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No students registered.")


# -------------------- ISSUE BOOK --------------------

elif menu == "Issue Book":

    st.subheader("Issue a Book")

    if not students:
        st.warning("Register a student before issuing a book.")

    elif not books:
        st.warning("Add a book before issuing it.")

    else:

        with st.form("issue_book_form"):

            roll = st.selectbox(
                "Select student",
                options=[s[0] for s in students],
                format_func=lambda x:
                    f"{x} — {find_student(x)[1]}"
            )

            book_id = st.selectbox(
                "Select book",
                options=[b[0] for b in books],
                format_func=lambda x:
                    f"{x} — {find_book(x)[1]} "
                    f"({find_book(x)[3]} available)"
            )

            st.info("One transaction issues 1 copy of the selected book.")

            submitted = st.form_submit_button(
                "Issue Book",
                type="primary"
            )

        if submitted:

            book = find_book(book_id)

            if active_issue_exists(roll, book_id):
                st.error("This student has already issued this book.")

            elif int(book[3]) <= 0:
                st.error("Sorry, no copies available right now.")

            else:

                issue_timestamp = current_time()

                book[3] = str(int(book[3]) - 1)

                records.append([
                    roll,
                    book_id,
                    "Issued",
                    issue_timestamp,
                    ""
                ])

                save_file(BOOKS_FILE, books)
                save_file(RECORDS_FILE, records)

                st.success(
                    "1 copy issued successfully! "
                    "Available stock has been updated."
                )

                st.info(f"Issue Date & Time: {issue_timestamp}")


# -------------------- RETURN BOOK --------------------

elif menu == "Return Book":

    st.subheader("Return a Book")

    active_records = [
        r for r in records
        if r[2] == "Issued"
    ]

    if not active_records:

        st.info("There are no active issued books to return.")

    else:

        labels = {
            (
                f"Roll {r[0]} • Book {r[1]} "
                f"• Issued: {r[3] or 'Time not recorded'}"
            ): r
            for r in active_records
        }

        with st.form("return_book_form"):

            selected = st.selectbox(
                "Select active issue",
                options=list(labels.keys())
            )

            submitted = st.form_submit_button(
                "Return Book",
                type="primary"
            )

        if submitted:

            record = labels[selected]
            book = find_book(record[1])

            if book is None:

                st.error("Book data is missing. Return cancelled.")

            else:

                return_timestamp = current_time()

                record[2] = "Returned"
                record[4] = return_timestamp

                book[3] = str(int(book[3]) + 1)

                save_file(BOOKS_FILE, books)
                save_file(RECORDS_FILE, records)

                st.success(
                    "Book returned successfully! "
                    "Available stock has been restored."
                )

                st.info(f"Return Date & Time: {return_timestamp}")


# -------------------- VIEW RECORDS --------------------

elif menu == "View Records":

    st.subheader("Borrowing Records")

    if records:

        st.dataframe(
            [
                {
                    "Roll Number": r[0],
                    "Book ID": r[1],
                    "Status": r[2],
                    "Issue Date & Time": r[3] or "Not recorded",
                    "Return Date & Time": r[4] or "Not returned"
                }
                for r in records
            ],
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No records yet.")


# -------------------- FOOTER --------------------

st.markdown("---")

st.markdown(
    '<p class="small-note">'
    'Library Management System • Demonstration interface • '
    'Data stored in books.txt, students.txt and records.txt'
    '</p>',
    unsafe_allow_html=True
)
