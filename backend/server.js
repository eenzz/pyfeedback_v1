import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import { lintPythonCode } from './lint/pythonLint.js';

const app = express();
app.use(cors());
app.use(bodyParser.json());

app.post('/lint', async (req, res) => {
    const { language, code } = req.body;

    if (!code || language !== 'python') {
        return res.status(400).json({ error: 'Invalid request: Python code expected' });
    }

    try {
        const lintResult = await lintPythonCode(code);
        res.json(lintResult);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

const PORT = process.env.PORT || 5006;
app.listen(PORT, () => {
    console.log(`✅ Linter API 서버 실행 중: http://localhost:${PORT}`);
});