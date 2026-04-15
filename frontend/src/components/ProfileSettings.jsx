import React, { useState, useEffect } from 'react';
import { getMe, updateMe, uploadAsset } from '../services/api';
import { useAuth } from '../context/AuthContext';
import './ProfileSettings.css';

const ProfileSettings = ({ isOpen, onClose }) => {
  const { setTeacher } = useAuth();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState({ header: false, footer: false });
  const [formData, setFormData] = useState({
    full_name: '',
    department: '',
    institution: '',
    default_session: '',
    default_semester: '',
    default_subject_name: '',
    default_subject_code: '',
  });

  useEffect(() => {
    if (isOpen) fetchUser();
  }, [isOpen]);

  const fetchUser = async () => {
    try {
      const { data } = await getMe();
      setUser(data);
      setFormData({
        full_name: data.full_name || '',
        department: data.department || '',
        institution: data.institution || 'Prestige Institute of Engineering, Management and Research, Indore',
        default_session: data.default_session || '',
        default_semester: data.default_semester || '',
        default_subject_name: data.default_subject_name || '',
        default_subject_code: data.default_subject_code || '',
      });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const [saveStatus, setSaveStatus] = useState(''); // 'saved' | 'error' | ''

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveStatus('');
    try {
      await updateMe(formData);
      // Always refetch from server to get the canonical saved data
      const { data: fresh } = await getMe();
      setTeacher({ ...fresh }); // Spread ensures a new object reference → triggers useEffect
      setUser(fresh);
      setSaveStatus('saved');
      setTimeout(() => {
        setSaveStatus('');
        onClose();
      }, 1200);
    } catch (err) {
      console.error('Save failed:', err.response?.data || err.message);
      setSaveStatus('error');
      alert(`Failed to save: ${JSON.stringify(err.response?.data || err.message)}`);
    } finally {
      setSaving(false);
    }
  };

  const handleFileUpload = async (e, type) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading({ ...uploading, [type]: true });
    const fd = new FormData();
    fd.append('file', file);
    fd.append('type', type);

    try {
      await uploadAsset(fd);
      await fetchUser(); // Refresh to show file ID or status
      alert(`${type.charAt(0).toUpperCase() + type.slice(1)} branding saved successfully and will be applied to all future documents.`);
    } catch (err) {
      alert('Upload failed');
    } finally {
      setUploading(prev => ({ ...prev, [type]: false }));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="settings-overlay">
      <div className="settings-card">
        <div className="settings-header">
          <h2>Academic Profile Settings</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        {loading ? (
          <div className="settings-loading">Loading...</div>
        ) : (
          <form onSubmit={handleSave} className="settings-form">
            <div className="form-section">
              <h3>Profile Information</h3>
              <div className="input-group">
                <label>Faculty Name</label>
                <input 
                  name="full_name" 
                  value={formData.full_name} 
                  onChange={handleChange} 
                  placeholder="Prof. Name"
                />
              </div>
              <div className="input-group">
                <label>Department</label>
                <input 
                  name="department" 
                  value={formData.department} 
                  onChange={handleChange} 
                  placeholder="e.g. Computer Science"
                />
              </div>
              <div className="input-group">
                <label>Institution</label>
                <input 
                  name="institution" 
                  value={formData.institution} 
                  onChange={handleChange} 
                />
              </div>
              <div className="input-group">
                <label>Default Session</label>
                <input 
                  name="default_session" 
                  value={formData.default_session} 
                  onChange={handleChange} 
                  placeholder="e.g. Jan-Jun 2026"
                />
              </div>
              <div className="input-group">
                <label>Default Semester</label>
                <input 
                  name="default_semester" 
                  value={formData.default_semester} 
                  onChange={handleChange} 
                  placeholder="e.g. 4th"
                />
              </div>
              <div className="input-group">
                <label>Default Subject Name</label>
                <input 
                  name="default_subject_name" 
                  value={formData.default_subject_name} 
                  onChange={handleChange} 
                  placeholder="e.g. Data Analysis"
                />
              </div>
              <div className="input-group">
                <label>Default Subject Code</label>
                <input 
                  name="default_subject_code" 
                  value={formData.default_subject_code} 
                  onChange={handleChange} 
                  placeholder="e.g. CS-101"
                />
              </div>
            </div>

            <div className="form-section">
              <h3>Branding Assets</h3>
              <p className="hint">Upload shared images (PNG/JPG) for document headers and footers.</p>
              
              <div className="asset-group">
                <div className="asset-info">
                  <label>Header Logo (Top of Doc)</label>
                  <span className={user.header_image_id ? "status-active" : "status-missing"}>
                    {user.header_image_id ? '✅ Saved & Active' : '❌ Not Uploaded'}
                  </span>
                </div>
                <div className="file-input-wrapper">
                  <input 
                    type="file" 
                    id="header-upload"
                    onChange={(e) => handleFileUpload(e, 'header')} 
                    disabled={uploading.header}
                    className="file-input"
                  />
                  <label htmlFor="header-upload" className="file-label">
                    {uploading.header ? 'Uploading...' : (user.header_image_id ? 'Change Header' : 'Upload Header')}
                  </label>
                </div>
              </div>

              <div className="asset-group">
                <div className="asset-info">
                  <label>Footer Asset (Bottom of Doc)</label>
                  <span className={user.footer_image_id ? "status-active" : "status-missing"}>
                    {user.footer_image_id ? '✅ Saved & Active' : '❌ Not Uploaded'}
                  </span>
                </div>
                <div className="file-input-wrapper">
                  <input 
                    type="file" 
                    id="footer-upload"
                    onChange={(e) => handleFileUpload(e, 'footer')} 
                    disabled={uploading.footer}
                    className="file-input"
                  />
                  <label htmlFor="footer-upload" className="file-label">
                    {uploading.footer ? 'Uploading...' : (user.footer_image_id ? 'Change Footer' : 'Upload Footer')}
                  </label>
                </div>
              </div>
            </div>

            <div className="settings-footer">
              <button type="button" className="cancel-btn" onClick={onClose}>Cancel</button>
              <button type="submit" className="save-btn" disabled={saving} style={{
                background: saveStatus === 'saved' ? '#16a34a' : saveStatus === 'error' ? '#dc2626' : undefined
              }}>
                {saving ? 'Saving...' : saveStatus === 'saved' ? '✅ Saved!' : saveStatus === 'error' ? '❌ Failed' : 'Save Settings'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ProfileSettings;
