import axios from 'axios';

const API_Base = 'http://localhost:8000';

export const analyzeMonolith = async (fileOrUrl) => {
    const formData = new FormData();
    if (fileOrUrl instanceof File) {
        formData.append('file', fileOrUrl);
    } else {
        formData.append('repo_url', fileOrUrl);
    }

    const response = await axios.post(`${API_Base}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
};

export const getStatus = async (jobId) => {
    const response = await axios.get(`${API_Base}/status/${jobId}`);
    return response.data;
};

export const getTree = async (jobId) => {
    const response = await axios.get(`${API_Base}/tree/${jobId}`);
    return response.data;
};

export const getReport = async (jobId) => {
    const response = await axios.get(`${API_Base}/report/${jobId}`);
    return response.data;
};

export const getResults = async (jobId) => {
    const response = await axios.get(`${API_Base}/results/${jobId}`);
    return response.data;
};
