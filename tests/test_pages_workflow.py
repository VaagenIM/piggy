"""Exercise the Pages artifact visibility gate without network or real waits."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/pages.yml"


@unittest.skipUnless(shutil.which("node"), "Node.js is required")
class PagesArtifactGateTest(unittest.TestCase):
    def gate(self, batches, artifact_id="42", artifact_name="github-pages-123-1"):
        workflow = WORKFLOW.read_text()
        script = re.search(r"          script: \|\n((?:            .*\n|\n)+)", workflow)[1]
        script = "\n".join(line[12:] for line in script.splitlines())
        harness = r"""
const fs = require('node:fs');
const {script, batches, artifactId, artifactName} = JSON.parse(fs.readFileSync(0, 'utf8'));
process.env.ARTIFACT_ID = artifactId;
process.env.ARTIFACT_NAME = artifactName;
let calls = 0, waits = 0;
const github = {
  rest: {actions: {listWorkflowRunArtifacts: {}}},
  paginate: async () => batches[Math.min(calls++, batches.length - 1)]
};
const context = {repo: {owner: 'example', repo: 'site'}, runId: 123};
const core = {info: () => {}};
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
(async () => {
  let error = null;
  try {
    await new AsyncFunction('github', 'context', 'core', 'setTimeout', script)(
      github, context, core, resolve => { waits++; resolve(); }
    );
  } catch (e) { error = e.message; }
  process.stdout.write(JSON.stringify({calls, waits, error}));
})();
"""
        result = subprocess.run(
            ["node", "-e", harness],
            input=json.dumps(dict(script=script, batches=batches, artifactId=artifact_id, artifactName=artifact_name)),
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(result.stdout)

    def artifact(self, **changes):
        return dict(id=42, name="github-pages-123-1", expired=False) | changes

    def test_waits_for_exact_uploaded_artifact(self):
        result = self.gate([[self.artifact(name="github-pages-old")], [], [self.artifact()]])
        self.assertEqual(result, dict(calls=3, waits=2, error=None))

    def test_duplicate_names_fail_before_deploy(self):
        result = self.gate([[self.artifact(), self.artifact(id=43)]])
        self.assertIn("Multiple artifacts", result["error"])
        self.assertEqual(result["waits"], 0)

    def test_wrong_id_and_expired_artifacts_are_not_used(self):
        result = self.gate([[self.artifact(id=43)], [self.artifact(expired=True)], [self.artifact()]])
        self.assertEqual(result, dict(calls=3, waits=2, error=None))

    def test_absence_times_out(self):
        result = self.gate([[]])
        self.assertEqual((result["calls"], result["waits"]), (12, 11))
        self.assertIn("was not discoverable", result["error"])

    def test_missing_build_output_fails_without_polling(self):
        result = self.gate([[]], artifact_id="")
        self.assertEqual(result["calls"], 0)
        self.assertIn("did not return", result["error"])


if __name__ == "__main__":
    unittest.main()
