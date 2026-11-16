# GitHub publication and updates

Repository: https://github.com/emmanuelsampson-prog/pharmacy-access-philadelphia  
GitHub Pages: https://emmanuelsampson-prog.github.io/pharmacy-access-philadelphia/

The release is labelled **public-data feasibility pilot**. A public website is a presentation of the research record, not evidence of a completed historical causal study.

## Update the project

Clone the repository, install `requirements-lock.txt` in Python 3.12, and follow the README. After changing the analysis, regenerate the notebooks, figures and web report. Review notebook outputs for restricted records before committing.

```bash
python -m src.download
python -m src.pilot
python -m pytest -q
python scripts/execute_notebooks.py
python scripts/build_website.py
git status --short
git add README.md index.html src scripts notebooks docs data/processed data/source_manifest.json outputs/public tests requirements*.txt
git diff --cached --stat
git diff --cached --name-only
git commit -m "Update reviewed public research outputs"
git push
```

Use `--inprocess` for notebook execution only in an environment that prohibits local kernel sockets. Do not force-push or overwrite unrelated work. Authenticate through GitHub's normal sign-in or an authorized CLI; never commit credentials.

## Web publication

The report is a single root `index.html`, generated from recorded outputs by `scripts/build_website.py`. Figures are embedded. It uses no analytics, third-party fonts, map tiles or visitor tracking. The emissions scenario calculator runs locally in the visitor's browser; its assumptions are not saved.

In **Settings → Pages**, select **Deploy from a branch**, branch **main**, folder **/(root)**, and save. `.nojekyll` makes this a static site. Check deployment and open the live URL before declaring an update published.

## Publication boundaries

Public notebooks, original code, references and public-source derived outputs are intended for publication. Raw downloads are available through acquisition code and the downloadable snapshot, but ignored in Git. Restricted mobility inputs and private outputs stay outside the public repository. Original code is MIT licensed; third-party sources retain their own terms.

The method-test workflow does not download data. The optional R estimator has not been executed. Successful tests or deployment do not establish causal identification.
