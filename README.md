# 🎓 Skillforge - Learning Path Dashboard

A full-stack web application built to help students learn courses, track progress, and receive learning materials, while instructors manage courses and admins control the entire system.

---

## ✅ Features

### 👨‍🎓 Learner
- Browse available courses
- Enroll into courses
- Access study material and lectures
- Attempt quizzes and give feedback
- View certificates and learning progress

### 👨‍🏫 Instructor
- Create and manage courses
- Upload materials, lectures, and quizzes
- Track student enrollment and progress
- Receive feedback on their courses

### 👩‍💼 Admin
- Manage learners, instructors, and courses
- Approve or remove users/courses
- Monitor entire platform activity
- Provide system support

---

## 📸 Preview Screens

| Page | Screenshot |
|------|------------|
| Home / Landing Page | ![](images/home.png) |
| Login & Signup | ![](images/auth.png) |
| Browse Courses | ![](images/courses.png) |
| Study  | ![](images/course-details.png) |
| Course view | ![](images/player.png) |
| Create Course | ![](images/create-course.png) |
| Ratings & Reviews | ![](images/ratings.png) |

> Add your actual images inside **/images** folder.

---

## 🚀 Features

### 👩‍🎓 Learner Features
- Browse & search courses  
- Enroll into free/paid courses  
- Watch video lectures  
- Download shared PDFs  
- Rate & review courses  

### 👨‍🏫 Instructor Features
- Create & publish courses  
- Upload thumbnails, videos, modules  
- Add PDFs, quizzes (optional)  
- Track course performance  
- Manage enrolled learners  

### 🛠️ Admin Features
- Manage users (learners & instructors)  
- Approve or block courses  
- Handle reports  
- System-level analytics  

---

## 🧩 Tech Stack

### **Frontend**
- HTML5  
- CSS3  
- JavaScript  
- Responsive UI

### **Backend**
- Python Flask  
- MySQL  

### **Other**
- Rating System  
- User Sessions  
- Access Control  
- Secure File Storage  

---

## 🏗️ Project Structure

```bash
project/
├── app.py
├── templates/
│   ├── index.html
│   ├── about.html
│   ├── contact.html
│   ├── login.html
    └── signup.html
│
│   ├── learner/
│   │   ├── dashboard.html
│   │   ├── courses.html
        └── study.html
│
│   ├── instructor/
│   │   ├── dashboard.html
        └── MyCourses.html
│
│   └── admin/
│       └── panel.html
│
├── static/
│   ├── css/
│   │   ├── style.css
│   ├── uploads/
│   │   ├── lectures
│   │   ├── pdfs
│   └── images
│
├── uploads/
│   ├── pdfs/
│   ├── images/
│   └── videos/
│
├── venv/              # your virtual environment
│
├── requirements.txt
├── README.md
└── .gitignore
