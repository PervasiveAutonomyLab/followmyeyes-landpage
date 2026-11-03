# Follow My Eyes project page

Project page for
[Follow My Eyes: Backdoor Attacks on Goal-Directed Scanpath Prediction](https://arxiv.org/abs/2604.08766) (WACV 2027).

It is a plain static page (HTML + CSS, Bulma from a CDN), so there is nothing to build.
It is served by GitHub Pages from the `main` branch at
https://pervasiveautonomylab.github.io/followmyeyes-landpage/.

## Running it locally

```
python -m http.server 8000
```

then open http://localhost:8000.

## Where things come from

- All text, numbers and tables come from the arXiv v2 LaTeX source (2604.08766v2, 1 Jul 2026).
- `static/images/*` were rendered from the paper's own PDF figures (same crops as the paper, except the overview
  figure, which keeps the bottom labels).
- `lab_logo.png` and `nsf_logo.png` are the lab and NSF logos.


## Citation

```bibtex
@inproceedings{romero2027followmyeyes,
  title     = {Follow My Eyes: Backdoor Attacks on Goal-Directed Scanpath Prediction},
  author    = {Romero, Diana and Ali, Mutahar and Khan, Momin Ahmad and Farrukh, Habiba and Anwar, Fatima and Elmalaki, Salma},
  booktitle = {Proceedings of the IEEE/CVF Winter Conference on Applications of Computer Vision (WACV)},
  year      = {2027}
}
```

## Videos

The four clips in `static/videos/` replay real GazeFormer predictions from the paper's qualitative figures.
Fixation positions and order are read from the vector paths in the figure PDFs; durations are the per-fixation
labels printed in the duration-inflation figures. To regenerate them from the arXiv source (`figures/` folder):

```
python tools/extract_scanpaths.py <arxiv_src>/figures extract.json
python tools/make_videos.py <arxiv_src>/figures extract.json static/videos <path-to-ffmpeg>
```

Each clip is saved as WebM and MP4 with a `.jpg` poster. `tools/render_figures.py` renders the still figures.
