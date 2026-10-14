# paper-schema

Source for the paper *Code availability is not enough: schemas for documenting
and extending data analysis* (H. Sherry Zhang and Roger D. Peng) and its
appendix. The paper proposes a schema that records a data analysis as a
sequence of decisions in natural language, from which an LLM generates and
validates analysis code. The schema is implemented in the R package
[`tines`](https://cran.r-project.org/package=tines).

## Repository structure

```
paper-schema/
├── paper-schema.qmd         main manuscript (Quarto source)
├── paper-schema.pdf         rendered manuscript
├── appendix.pdf             rendered appendix
├── bibliography.bib         references for both documents
├── schemas/                 schemas, alternative files and scripts shown in the paper
├── figures/                 Figure 1 (workflow diagram) and the script that draws it
├── data/                    saved model output used during development
├── sim-football/            submodule: many-analysts football study pipeline
├── latex/                   AOAS template: IMS class (imsart), bibliography style,
│                            and the Quarto partials the manuscript renders with
└── apa.csl                  citation style for the appendix
```

