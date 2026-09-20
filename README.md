# StudyGenie — AI-Powered Student Assistant

StudyGenie is an AI-powered academic assistant designed to help college students manage their studies, understand academic concepts, practice through quizzes, organize tasks, and receive personalized study recommendations.

The project combines **Artificial Intelligence, automation, task management, quiz generation, progress analytics, and study notes** into a single web application.

---

## 📌 Project Overview

College students often use multiple applications for managing assignments, preparing for exams, practicing questions, taking notes, and tracking their academic progress.

StudyGenie provides these features in one platform.

The system allows students to:

- Manage academic tasks and deadlines
- Generate AI-powered quizzes
- Evaluate quiz performance
- Ask academic questions to an AI assistant
- Upload and manage PDF study notes
- Ask questions from uploaded notes
- Track academic progress
- Receive AI-generated study recommendations
- Receive automated alerts based on tasks and quiz performance

---

## 🎯 Objectives

The main objectives of StudyGenie are:

1. To provide students with a centralized academic assistance platform.
2. To use AI to generate useful academic content.
3. To help students practice topics through automatically generated quizzes.
4. To track tasks, deadlines, and quiz performance.
5. To analyze student activity and provide personalized study recommendations.
6. To automate academic alerts based on deadlines and performance.
7. To provide an easy-to-use and student-friendly interface.

---

## ✨ Features

### 🔐 User Authentication

Students can create an account and securely log in to StudyGenie.

Student profile information includes:

- Name
- Email
- College
- Course
- Branch
- Semester

Passwords are stored using password hashing.

---

### 📊 Student Dashboard

The dashboard provides an overview of the student's academic activity.

It displays:

- Pending tasks
- Upcoming deadlines
- Number of quizzes taken
- Average quiz score
- Upcoming tasks
- Recent quiz performance
- AI study recommendations
- Smart alerts

---

### ✅ Task Management

Students can create and manage academic tasks.

Each task can contain:

- Task title
- Description
- Subject
- Due date
- Priority
- Completion status

Students can:

- Add tasks
- Mark tasks as completed
- Delete tasks

---

### 🤖 AI Quiz Generator

StudyGenie can generate multiple-choice quizzes using AI.

Students can provide a topic such as:

- DBMS
- Data Structures
- Python
- Operating Systems
- Computer Networks

The AI generates questions with:

- Question
- Four options
- Correct answer

The generated questions are stored in the database.

---

### 📝 Quiz Evaluation

Students can attempt generated quizzes and submit their answers.

StudyGenie automatically:

- Evaluates answers
- Calculates the score
- Stores quiz results
- Displays the final score
- Maintains quiz history

---

### 🧠 AI Academic Assistant

StudyGenie includes an AI academic assistant that can help students with:

- Academic concepts
- Programming questions
- Assignments
- Exam preparation
- Study planning

The assistant can also use the student's academic profile as context when generating responses.

---

### 📚 Study Notes

Students can upload PDF study notes.

StudyGenie extracts text from uploaded documents and stores the extracted content.

Students can:

- Upload notes
- View extracted notes
- Ask questions about the uploaded content
- Delete notes

---

### 📈 Student Progress Analytics

The progress module provides an overview of academic performance.

It includes:

- Total tasks
- Completed tasks
- Pending tasks
- Number of quizzes
- Average quiz score
- Topic-wise quiz performance
- Recent quiz performance
- Visual charts

This allows students to monitor their academic activity and quiz performance.

---

### 💡 AI Study Recommendations

StudyGenie analyzes:

- Student profile
- Tasks
- Deadlines
- Quiz history
- Quiz performance

Based on this information, the AI generates:

- Academic summary
- Priority recommendations
- Topics needing attention
- Strong topics
- Recommended study plan

---

### ⚡ Smart Automation & Alerts

The Smart Automation module analyzes the student's academic activity and generates useful alerts.

Alerts can be related to:

- Upcoming deadlines
- High-priority tasks
- Multiple pending tasks
- Quiz performance
- Topics requiring revision
- General study recommendations

Alerts are categorized by priority:

- High
- Medium
- Low

This provides an automation layer on top of the student's academic data.

---

## 🛠️ Technology Stack

### Frontend

- HTML5
- CSS3
- JavaScript

### Backend

- Python
- Flask

### Database

- MySQL

### Artificial Intelligence

- OpenAI API

### Authentication

- bcrypt

### PDF Processing

- pypdf
- pdf2image
- Pillow
- Tesseract OCR

### Development Tools

- Git
- GitHub
- Python Virtual Environment

---

## 🏗️ System Architecture

The basic architecture of StudyGenie is:

```text
                  ┌─────────────────────┐
                  │       Student       │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   HTML / CSS / JS   │
                  │      Frontend       │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │      Flask App      │
                  │       Backend       │
                  └───────┬─────┬───────┘
                          │     │
              ┌───────────┘     └────────────┐
              ▼                              ▼
     ┌─────────────────┐             ┌─────────────────┐
     │      MySQL      │             │   OpenAI API    │
     │    Database     │             │       AI        │
     └─────────────────┘             └─────────────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │ AI Features         │
                                  │                     │
                                  │ • Quiz Generation   │
                                  │ • AI Assistant      │
                                  │ • Recommendations   │
                                  │ • Smart Alerts      │
                                  └─────────────────────┘
                                  