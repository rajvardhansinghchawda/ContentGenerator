import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import './GenerationForm.css'

const DIFFICULTY_OPTIONS = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
]

const QUESTION_TYPES = [
  { value: 'MCQ', label: 'MCQ' },
  { value: 'SHORT', label: 'Short Answer' },
  { value: 'MIXED', label: 'Mixed' },
]

export default function GenerationForm({ onSubmit, disabled }) {
  const { teacher } = useAuth()
  const [form, setForm] = useState({
    topic: '',
    subject_name: '',
    subject_code: '',
    class_section: '',
    difficulty: 'medium',
    num_questions: 10,
    marks_per_question: 2,
    question_type: 'MCQ',
    additional_notes: '',
    lecture_no: '',
    session: '',
    semester: '',
  })


  useEffect(() => {
    if (teacher) {
      setForm(prev => ({
        ...prev,
        session: teacher.default_session || prev.session,
        semester: teacher.default_semester || prev.semester,
        subject_name: teacher.default_subject_name || prev.subject_name,
        subject_code: teacher.default_subject_code || prev.subject_code,
      }))
    }
  }, [teacher])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!form.topic.trim()) return

    const payload = {
      topic: form.topic,
      difficulty: form.difficulty,
      num_questions: form.num_questions,
      marks_per_question: form.marks_per_question,
      question_type: form.question_type,
      additional_notes: form.additional_notes,
      lecture_no: form.lecture_no,
      session: form.session,
      semester: form.semester,
      subject_name: form.subject_name,
      subject_code: form.subject_code,
    }

    onSubmit(payload)
  }

  return (
    <form className="generation-form" onSubmit={handleSubmit}>
      <div className="form-header">
        <span className="material-icons-outlined form-header-icon">auto_awesome</span>
        <div>
          <h2 className="headline-md">Generate New Content</h2>
          <p className="body-md" style={{ color: 'var(--on-surface-variant)', marginTop: 4 }}>
            Define your academic parameters and let the curator craft your material.
          </p>
        </div>
      </div>

      <div className="form-grid">
        {/* Topic */}
        <div className="form-group form-col-full">
          <label className="form-label" htmlFor="topic">Topic *</label>
          <input
            id="topic"
            className="form-input"
            type="text"
            name="topic"
            value={form.topic}
            onChange={handleChange}
            placeholder="e.g. Neural Networks: The Fundamentals"
            required
            disabled={disabled}
          />
        </div>

        {/* Subject, Lecture, Session */}
        <div className="form-group">
          <label className="form-label" htmlFor="subject_name">Subject Name</label>
          <input
            id="subject_name"
            className="form-input"
            type="text"
            name="subject_name"
            placeholder="e.g. Data Analysis"
            value={form.subject_name}
            onChange={handleChange}
            disabled={disabled}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="subject_code">Subject Code</label>
          <input
            id="subject_code"
            className="form-input"
            type="text"
            name="subject_code"
            placeholder="e.g. CS-101"
            value={form.subject_code}
            onChange={handleChange}
            disabled={disabled}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="lecture_no">Lecture No.</label>
          <input
            id="lecture_no"
            className="form-input"
            type="text"
            name="lecture_no"
            placeholder="e.g. 05"
            value={form.lecture_no}
            onChange={handleChange}
            disabled={disabled}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="session">Session</label>
          <input
            id="session"
            className="form-input"
            type="text"
            name="session"
            placeholder="e.g. Jan-Jun 2026"
            value={form.session}
            onChange={handleChange}
            disabled={disabled}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="semester">Semester</label>
          <input
            id="semester"
            className="form-input"
            type="text"
            name="semester"
            placeholder="e.g. 4th"
            value={form.semester}
            onChange={handleChange}
            disabled={disabled}
          />
        </div>

        {/* Class/Section */}
        <div className="form-group">
          <label className="form-label" htmlFor="class_section">Class / Section</label>
          <input
            id="class_section"
            className="form-input"
            type="text"
            name="class_section"
            value={form.class_section}
            onChange={handleChange}
            placeholder="e.g. CS-301A"
            disabled={disabled}
          />
        </div>

        {/* Difficulty */}
        <div className="form-group">
          <label className="form-label" htmlFor="difficulty">Difficulty</label>
          <select
            id="difficulty"
            className="form-select"
            name="difficulty"
            value={form.difficulty}
            onChange={handleChange}
            disabled={disabled}
          >
            {DIFFICULTY_OPTIONS.map(d => (
              <option key={d.value} value={d.value}>{d.label}</option>
            ))}
          </select>
        </div>

        {/* Number of Questions */}
        <div className="form-group">
          <label className="form-label" htmlFor="num_questions">Number of Questions</label>
          <input
            id="num_questions"
            className="form-input"
            type="number"
            name="num_questions"
            value={form.num_questions}
            onChange={handleChange}
            min={1}
            max={100}
            disabled={disabled}
          />
        </div>

        {/* Marks per Question */}
        <div className="form-group">
          <label className="form-label" htmlFor="marks_per_question">Marks per Question</label>
          <input
            id="marks_per_question"
            className="form-input"
            type="number"
            name="marks_per_question"
            value={form.marks_per_question}
            onChange={handleChange}
            min={1}
            max={100}
            disabled={disabled}
          />
        </div>

        {/* Question Type */}
        <div className="form-group form-col-full">
          <label className="form-label">Question Type</label>
          <div className="radio-group">
            {QUESTION_TYPES.map(qt => (
              <div className="radio-pill" key={qt.value}>
                <input
                  type="radio"
                  name="question_type"
                  id={`qt-${qt.value}`}
                  value={qt.value}
                  checked={form.question_type === qt.value}
                  onChange={handleChange}
                  disabled={disabled}
                />
                <label htmlFor={`qt-${qt.value}`}>{qt.label}</label>
              </div>
            ))}
          </div>
        </div>

        {/* Additional Notes */}
        <div className="form-group form-col-full">
          <label className="form-label" htmlFor="additional_notes">Additional Notes</label>
          <textarea
            id="additional_notes"
            className="form-textarea"
            name="additional_notes"
            value={form.additional_notes}
            onChange={handleChange}
            placeholder="Any specific instructions for the AI..."
            disabled={disabled}
          />
        </div>
      </div>

      <button
        type="submit"
        className="btn btn-primary btn-lg generation-submit"
        disabled={disabled || !form.topic.trim()}
      >
        <span className="material-icons-outlined">rocket_launch</span>
        Generate Pre-Doc, Post-Doc & Quiz
      </button>
    </form>
  )
}
