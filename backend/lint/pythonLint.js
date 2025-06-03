import { exec as execCallback } from 'child_process';
import { writeFile, unlink } from 'fs/promises';
import path from 'path';
import os from 'os';
import { promisify } from 'util';

const exec = promisify(execCallback);

export async function lintPythonCode(code) {
    const tempFile = path.join(os.tmpdir(), `lint_${Date.now()}.py`);
    await writeFile(tempFile, code, 'utf8');

    try {
        const { stdout, stderr } = await exec(`python3 -m pylint ${tempFile} -rn -sn`, { timeout: 5000 });
        const output = stdout || stderr;

        const feedback = output
            .split('\n')
            .filter(line => line.trim() !== '')
            .map(line => line.trim());

        return { feedback };
    } catch (error) {
        const output = error.stdout || error.stderr || error.message;
        const feedback = output
            .split('\n')
            .filter(line => line.trim() !== '')
            .map(line => line.trim());

        // "에러지만" 결과는 반환하도록!
        return { feedback };
    } finally {
        await unlink(tempFile);
    }
}