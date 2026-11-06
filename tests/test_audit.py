import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from gesture_recognition_claim_audit.audit import audit, evidence, main, matches, GESTURERECOGNITION, NOGESTURERECOGNITION, GENERIC_NAMES

class AuditTests(unittest.TestCase):
    def test_phrase_oracle(self):
        self.assertEqual(list(GESTURERECOGNITION), ['gesture recognition', 'gesture-recognition', 'hand gesture recognition', 'hand-gesture recognition', 'recognizes gestures', 'recognize gestures', 'recognizing gestures', 'recognized gestures', 'recognize hand gestures', 'recognizes hand gestures', 'recognizing hand gestures', 'gesture recognition support', 'supports gesture recognition', 'gesture recognition capability', 'gesture recognition feature', 'gesture recognition pipeline', 'gesture recognition system', 'gesture recognition tool', 'gesture recognition framework', 'gesture recognition library', 'gesture recognition api', 'gesture recognition model', 'gesture recognition models', 'gesture recognition engine', 'gesture recognition module', 'gesture recognition function', 'gesture recognition functionality', 'gesture recognition workflow', 'gesture recognition method', 'gesture recognition approach', 'gesture recognition service', 'gesture recognition results', 'gesture recognition performance', 'gesture recognition task', 'gesture recognition tasks', 'gesture recognition algorithm', 'gesture recognition algorithms', 'gesture recognition configuration', 'gesture recognition script', 'read gestures', 'reads gestures', 'reading gestures', 'detect hand gestures', 'detects hand gestures', 'detecting hand gestures', 'gesture recognition mode', 'recognize sign language', 'sign language recognition', 'sign-language recognition', 'convert gestures to text'])
        self.assertEqual(list(NOGESTURERECOGNITION), ['does not recognize gestures', 'do not recognize gestures', "doesn't recognize gestures", "don't recognize gestures", 'no gesture recognition', 'without gesture recognition', 'never recognizes gestures', 'does not support gesture recognition', 'gesture recognition not supported', 'gesture recognition unsupported', 'no gesture recognition support', 'lacks gesture recognition', 'missing gesture recognition', 'gesture recognition disabled', 'no gesture recognition model', 'without gesture recognition support', 'does not provide gesture recognition', 'no automatic gesture recognition', 'gesture recognition not available', 'no gesture recognition capability', 'does not recognize hand gestures', 'without a gesture recognition model', 'does not perform gesture recognition', 'never performs gesture recognition'])

    def test_generic_oracle(self):
        self.assertEqual(list(GENERIC_NAMES), ['recognize_gesture', 'recognize_gestures', 'detect_gesture', 'detect_gestures', 'classify_gesture', 'classify_gestures', 'recognize_hand_gesture', 'recognize_hand_gestures', 'detect_hand_gesture', 'recognize_sign_language', 'recognize_sign', 'translate_sign_language', 'detect_sign_language', 'gesture_recognition', 'hand_gesture_recognition', 'recognize_motion_gesture', 'predict_gesture', 'predict_gestures', 'identify_gesture', 'identify_gestures', 'parse_gesture', 'get_gesture', 'extract_gesture', 'process_gesture'])

    def fixture(self, readme='', code='', extra=None, flags=()):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'README.md').write_text(readme)
            (root/'app.py').write_text(code)
            for name, text in (extra or {}).items():
                p = root/name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = main(['audit', str(root)] + list(flags))
            return status, out.getvalue()

    def test_inventory_matching(self):
        for phrase in GESTURERECOGNITION:
            with self.subTest(phrase=phrase):
                self.assertEqual(matches(phrase, GESTURERECOGNITION)[0], [phrase])
        for phrase in NOGESTURERECOGNITION:
            with self.subTest(phrase=phrase):
                denials, rest = matches(phrase, NOGESTURERECOGNITION)
                self.assertEqual(denials, [phrase])
                self.assertEqual(matches(rest, GESTURERECOGNITION)[0], [])
        self.assertEqual(matches('hand gesture recognition', GESTURERECOGNITION)[0], ['hand gesture recognition'])

    def test_generics(self):
        for name in GENERIC_NAMES:
            for code in ('x.'+name+'()', 'from unknown import '+name+'; '+name+'()', 'from unknown import '+name+' as run; run()'):
                with self.subTest(code=code): self.assertTrue(evidence(code))

    def test_split_modules(self):
        self.assertEqual(self.fixture('gesture recognition', 'import mediapipe as mp; m=mp.tasks.vision.GestureRecognizer()', {'other.py': 'm.recognize(x)'})[0], 2)

    def test_matching(self):
        self.assertEqual(matches('gesture recognition', GESTURERECOGNITION)[0], ['gesture recognition'])
        self.assertEqual(self.fixture('does not recognize gestures')[0], 0)
        self.assertEqual(self.fixture('GESTURE RECOGNITION')[0], 2)
        self.assertEqual(self.fixture('```text\ngesture recognition\n```')[0], 0)
        self.assertEqual(self.fixture('`gesture recognition`')[0], 2)
        self.assertEqual(matches('she reads gestures better than words', GESTURERECOGNITION)[0], ['reads gestures'])

    def test_cli_good(self):
        self.assertEqual(self.fixture('gesture recognition', 'x.recognize_gesture()'), (0, 'PASS\n'))

    def test_cli_bad(self):
        status, out = self.fixture('gesture recognition')
        self.assertEqual(status, 2)
        self.assertIn('HIGH documented-gesture-recognition-claim-false', out)

    def test_cli_test_only(self):
        extra = {'tests/sample.md': 'gesture recognition'}
        status, out = self.fixture(extra=extra)
        self.assertEqual(status, 0)
        self.assertIn('MEDIUM', out)
        self.assertEqual(self.fixture(extra=extra, flags=['--fail-on', 'medium'])[0], 2)

    def test_cli_denial(self):
        status, out = self.fixture('no gesture recognition', 'x.recognize_gesture()')
        self.assertEqual(status, 2)
        self.assertIn('HIGH documented-no-gesture-recognition-claim-false', out)

    def test_cli_no_claim(self):
        self.assertEqual(self.fixture('A useful tool.'), (0, 'PASS\n'))

    def test_cli_json(self):
        status, out = self.fixture('gesture recognition', flags=['--json'])
        f = json.loads(out)[0]
        self.assertEqual(status, 2)
        self.assertEqual(f['verdict'], 'FAIL')
        self.assertTrue(f['message'])

    def test_cli_ignore(self):
        self.assertEqual(self.fixture(extra={'docs/claim.md': 'gesture recognition'}, flags=['--ignore', 'docs/'])[0], 0)

    def test_cli_version(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as cm:
            main(['--version'])
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), '0.1.0')

    def test_readme(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(self.fixture((root/'README.md').read_text()), (0, 'PASS\n'))

    def test_io_and_usage(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['audit', '/nonexistent-r142-directory']), 1)
            with self.assertRaises(SystemExit) as cm: main(['audit', '--unknown'])
        self.assertEqual(cm.exception.code, 1)

    def test_virtualenv_excluded(self):
        status, out = self.fixture('gesture recognition', extra={
            'custom-env/pyvenv.cfg': 'home = /usr/bin',
            'custom-env/lib/model.py': 'x.recognize_gesture()',
        })
        self.assertEqual(status, 2)

    def test_verbose(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(self.fixture(flags=['--verbose'])[0], 0)
        self.assertIn('scope:', err.getvalue())

    def test_recognizer_pairs(self):
        for setup, factory in [
            ('import mediapipe as mp;', 'mp.tasks.vision.GestureRecognizer'),
            ('from mediapipe.tasks import python;', 'python.vision.GestureRecognizer'),
            ('from mediapipe.tasks.python.vision import GestureRecognizer;', 'GestureRecognizer'),
            ('from mediapipe.tasks.python.vision import GestureRecognizer as GR;', 'GR'),
        ]:
            for construction in (factory+'()', factory+'.create_from_options(opts)'):
                for method in ('recognize', 'recognize_for_video', 'recognize_async'):
                    for expression in ('r='+construction+'; r.'+method+'(x)', construction+'.'+method+'(x)'):
                        with self.subTest(expression=expression):
                            self.assertTrue(evidence(setup+expression))
                self.assertFalse(evidence(setup+construction))
                self.assertFalse(evidence(setup+'r='+construction+'; other.recognize(x)'))

    def test_hands_pairs(self):
        for setup, factory in [
            ('import mediapipe as mp;', 'mp.solutions.hands.Hands'),
            ('from mediapipe.solutions.hands import Hands;', 'Hands'),
            ('from mediapipe.solutions.hands import Hands as H;', 'H'),
            ('import mediapipe.solutions.hands as h;', 'h.Hands'),
        ]:
            self.assertTrue(evidence(setup+'h='+factory+'(); h.process(x)'))
            self.assertTrue(evidence(setup+factory+'().process(x)'))
            self.assertFalse(evidence(setup+factory+'()'))
            self.assertFalse(evidence(setup+'h='+factory+'(); other.process(x)'))
        self.assertTrue(evidence('import mediapipe as mp\nwith mp.solutions.hands.Hands() as h:\n h.process(x)'))

    def test_opencv_pairs(self):
        for setup, a, b in [
            ('import cv2;', 'cv2.findContours', 'cv2.convexityDefects'),
            ('import cv2 as c;', 'c.findContours', 'c.convexityDefects'),
            ('from cv2 import findContours, convexityDefects;', 'findContours', 'convexityDefects'),
            ('from cv2 import findContours as F, convexityDefects as D;', 'F', 'D'),
        ]:
            self.assertTrue(evidence(setup+a+'(x); '+b+'(x)'))
            self.assertFalse(evidence(setup+a+'(x)'))
            self.assertFalse(evidence(setup+b+'(x)'))
        self.assertEqual(self.fixture('gesture recognition', 'import cv2; cv2.findContours(x)', {'other.py':'import cv2; cv2.convexityDefects(x)'})[0], 2)

    def test_leap_pairs(self):
        for setup, factory in [('import Leap;', 'Leap.Controller'), ('import Leap as L;', 'L.Controller'), ('from Leap import Controller;', 'Controller'), ('from Leap import Controller as C;', 'C')]:
            for expression in ('c='+factory+'(); f=c.frame(); f.gestures()', factory+'().frame().gestures()'):
                self.assertTrue(evidence(setup+expression))
            self.assertFalse(evidence(setup+factory+'()'))
            self.assertFalse(evidence(setup+'c='+factory+'(); other.frame().gestures()'))
            self.assertFalse(evidence(setup+'c='+factory+'(); other.gestures()'))

    def test_shadowing(self):
        for definition in ('def', 'class'):
            body = '(): pass' if definition == 'def' else ': pass'
            for name, setup, call in [
                ('recognize_gesture', 'from lib import recognize_gesture', 'recognize_gesture()'),
                ('GestureRecognizer', 'from mediapipe.tasks.python.vision import GestureRecognizer', 'GestureRecognizer().recognize(x)'),
                ('Hands', 'from mediapipe.solutions.hands import Hands', 'Hands().process(x)'),
                ('Controller', 'from Leap import Controller', 'Controller().frame().gestures()'),
                ('findContours', 'from cv2 import findContours, convexityDefects', 'findContours(x); convexityDefects(x)'),
                ('convexityDefects', 'from cv2 import findContours, convexityDefects', 'findContours(x); convexityDefects(x)'),
            ]:
                with self.subTest(name=name, definition=definition):
                    self.assertFalse(evidence(setup+'\n'+definition+' '+name+body+'\n'+call))
        self.assertFalse(evidence('import mediapipe as mp\nclass GestureRecognizer: pass\nmp.tasks.vision.GestureRecognizer().recognize(x)'))
        self.assertFalse(evidence('from mediapipe.tasks.python.vision import GestureRecognizer as GR\nclass GestureRecognizer: pass\nGR().recognize(x)'))
        self.assertFalse(evidence('from cv2 import findContours as F, convexityDefects as D\ndef findContours(): pass\nF(x); D(x)'))
        self.assertFalse(evidence('from lib import recognize_gesture as r\ndef recognize_gesture(): pass\nr()'))

    def test_rejections(self):
        cases = [
            'import mediapipe, cv2, Leap',
            'import mediapipe as mp; mp.solutions.pose.Pose().process(x)',
            'import mediapipe as mp; mp.solutions.face_detection.FaceDetection().process(x)',
            'import face_recognition; face_recognition.face_encodings(x)',
            'from ultralytics import YOLO; YOLO().predict(x)',
            'g=GestureDetector(); g.on_swipe(x); g.on_pinch(x); g.on_tap(x)',
            'r.recognize(x); h.process(x); f.gestures()',
            '"gesture recognition recognize gestures" # recognize gestures',
            '"""recognize gestures"""',
            'from lib import recognize_gesture; recognize_gesture',
            'recognize_gesture()',
            'import subprocess; subprocess.run(["recognition-cli", "input"])',
            'this is invalid python!',
        ]
        for code in cases:
            with self.subTest(code=code): self.assertFalse(evidence(code))

    def test_longest_and_scope(self):
        self.assertEqual(matches('convert gestures to text', GESTURERECOGNITION)[0], ['convert gestures to text'])
        self.assertEqual(matches('hand gesture recognition', GESTURERECOGNITION)[0], ['hand gesture recognition'])
        self.assertEqual(self.fixture(extra={'docs/nested/a.md':'gesture recognition'})[0], 2)
        self.assertEqual(self.fixture(extra={'other.md':'gesture recognition'})[0], 0)
        self.assertEqual(self.fixture('no gesture recognition')[0], 0)
        self.assertEqual(self.fixture('gesture recognition', 'import mediapipe as mp; h=mp.solutions.hands.Hands()', {'other.py':'h.process(x)'})[0], 2)
        self.assertEqual(self.fixture('gesture recognition', 'import Leap; c=Leap.Controller()', {'other.py':'c.frame().gestures()'})[0], 2)

if __name__ == '__main__':
    unittest.main()
