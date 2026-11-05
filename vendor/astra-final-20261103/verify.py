"""Offline test harness. Run with -B; all writable artifacts stay in this package."""
import sys
sys.dont_write_bytecode = True
import io
import json
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
blocked = []


def inside(path):
    if isinstance(path, int) or path is None:
        return
    if not Path(os.fsdecode(path)).resolve().is_relative_to(ROOT):
        raise PermissionError('verification write outside final package refused')


def offline_guard(event, args):
    if event.startswith(('socket.', 'subprocess.')) or event in ('os.system', 'os.exec', 'os.posix_spawn'):
        blocked.append(event)
        raise PermissionError('offline verification refuses external I/O: ' + event)
    if event == 'open':
        path, mode, flags = args
        if (mode and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            inside(path)
    if event == 'sqlite3.connect':
        inside(args[0])
    if event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.truncate', 'os.utime'):
        # Python shutil uses dir_fd-relative basenames; the sandbox supplies the outer boundary.
        if len(args) and (Path(os.fsdecode(args[0])).is_absolute() or not isinstance(args[-1], int) or args[-1] == -1):
            inside(args[0])
    if event in ('os.rename', 'os.link', 'os.symlink'):
        inside(args[0])
        inside(args[1])


def main():
    sys.addaudithook(offline_guard)
    from astra_lifecycle.contracts import file_hash
    from astra_lifecycle.integration import run_audit
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (ROOT / 'reports/test-results.txt').write_text(stream.getvalue())
    audit = run_audit()
    (ROOT / 'reports/adapter-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    baseline = json.loads((ROOT / 'reports/source-baseline.json').read_text())
    checks = [row | {'unchanged': Path(row['path']).is_file() and file_hash(row['path']) == row['sha256']} for row in baseline]
    integrity = {'status': 'PASS' if all(r['unchanged'] for r in checks) else 'FAIL', 'sources': checks}
    (ROOT / 'reports/source-integrity.json').write_text(json.dumps(integrity, indent=2) + '\n')
    summary = dict(status='PASS' if result.wasSuccessful() and audit['status'] == integrity['status'] == 'PASS' and not blocked else 'FAIL',
                   tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
                   adapter_audit=audit['status'], source_integrity=integrity['status'], blocked_external_attempts=blocked,
                   mode='offline-fixture', network_calls=0, paid_renders=0, live_air=False, spend_cents=0)
    (ROOT / 'reports/verification.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    if not result.wasSuccessful():
        print(stream.getvalue()[-14000:])
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
