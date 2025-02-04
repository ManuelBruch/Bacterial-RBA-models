*Ralstonia eutropha H16* RBA model
================
Michael Jahn,
2021-10-20

***

## Overview

This resource balance analysis (RBA) model was generated using the [RBApy package from Bulovic et al.](https://doi.org/10.1016/j.ymben.2019.06.001), using a genomse scale metabolic model (GSM) originally developed by [Park et al., 2011](http://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-5-101). The original genome scale model was refurbished, curated many reactions and harmonizing the model with community standards as e.g. available through the [Bigg model database](bigg.ucsd.edu/). The genome scale model that serves as base for the RBA model is maintained on [github.com/m-jahn/](https://github.com/m-jahn/genome-scale-models).

The RBA model is an extension of the GSM where the solution space is constrained by many additional parameters. Model construction and parameter estimation are described below in more detail. Parameter estimation was largely based on the following publications:

 - [Bulovic et al., 2019](https://doi.org/10.1016/j.ymben.2019.06.001): automatic model creation workflow; rates for translation, protein folding, and other minor functions.
 - [Park et al., 2011](http://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-5-101): cell composition of *R. eutropha* (original biomass equation), original genome scale model.

<p align="center">
  <img src="figures/RBA_model_generation.png" />
</p>

----------

## Generation of the XML model

### Step 1: Making a default model

For initial creation of the RBA model, the following input files were used. The fasta file headers were formatted according to the pattern `rba|id|name|set_name|stoichiometry`.

 - `data/sbml.xml`: genome scale metabolic model in SBML format. Some minor modifications were made to make it fit before RBA model construction (see `generate_model.py`). For example, empty gene associations were replaced with `UNKNOWN` to prevent RBA reading those reactions as spontaneous.
 - `data/ribosome.fasta`: composition of ribosome (rRNA and proteins). rRNA sequences were retrieved from NCBI, ribosomal protein sequence and subunit structure from uniprot. 68 ribosomal proteins were included. Ribosomal stoichiometry was assumed to be one subunit each for 30S and 50S subunits, except for L7/L12 that forms 2-4 dimers per ribosome (`n >= 4`).
 - `data/chaperones.fasta`: composition of molecular machines involved in protein folding. These include the protein subunits `groES`, `groEL`, `dnaJ`, `dnaK`, `grpE`, `trigger factor tig`, `htpG`, and `hfq` with their respective number of subunits obtained from uniprot.
 - `data/trnas.fasta`: composition of tRNAs. tRNA sequences were retrieved from NCBI, and only one representative tRNA (the first) per amino acid was used (20 out of 61 tRNAs).
 - `params.in`: pipeline parameters, most notably uniprot's `ORGANISM_ID = 381666`

To make a preliminary model with helper files, run the following code in python3:

```{python}
import rba

# generate model
reutropha = rba.RbaModel.from_data('params.in')

# export to disk
reutropha.write()
```

### Step 2: Generation of a model improved through helper files

The previous step downloaded `data/uniprot.csv`, generated helper files `data/*.tsv`, and generated a first XML model. The following modifications were then made to helper files.

 - `location_map.tsv`: the uniprot compartment names were mapped to generic names (such as `Cytoplasm`)
 - `metabolites.tsv`: this table contains target metabolite concentrations for basic biomolecules and cofactors (for example `ATP`, `dATP`, `thiamin`, and so on). Molecules that are already contained in macrocomponents were set to zero. One exception are some nucleotide species that are present in more detail compared to macrocomponent reactions.
 - `macrocomponents.tsv`: This table was supplemented with all major cell components (such as lipopolysaccharides, peptidoglycan, cofactors, and so on) and corresponding target concentrations from the original model's biomass equation.
 - `medium.tsv`: added new minimal medium.
 - `subunits.tsv`: updated some protein stoichiometries (ATP synthase).
 - `unknown_proteins.tsv`: (empty) the SBML model contains no genes that could not be mapped

Two additional macro-processes were added, **transcription of DNA to mRNA**, and **DNA replication**. 
The RBApy source code was adapted to automatically load protein associations from `transcription.fasta` and `replication.fasta` (see [github fork 'extra processes'](https://github.com/m-jahn/RBApy/tree/extra_processes)). 

#### Machinery for transcription (TSC)

 - The **transcription rate per RNA polymerase unit** was added to the parameter set. On bionumbers, several values in the range of 20-80 nt per second are given. We take the most recent estimate for *E. coli*, 62 nt/s or 223200 nt/h ([Epshtein & Nudler E, Science, 2003](https://pubmed.ncbi.nlm.nih.gov/12730602/).
- **Proteins that catalyze transcription** (RNA polymerase complex) were added. The canonical RNA polymerase in bacteria consists of 2 alpha, 1 beta, 1 beta prime, and 1 omega subunit. When a sigma factor is associated with the core, the holoenzyme is formed, which can initiate transcription. Four proteins were added as important sigma factors, rpoD1, D2, rpoS, and rpoN, each with partial contribution of 0.25 (source: Uniprot).

#### Machinery for replication (REP)

- DNA replication is mainly catalyzed by **DNA-dependent DNA polymerase III**. Bionumbers gives different rate estimates from 600-1000 nt/s ((bionumber IDs 102052, 104938, 109251, 111770)), on average around 800 nt/s or 2880000 nt/h.
- DNA polymerase III contains a core (composed of alpha, epsilon and theta chains) that associates with a tau subunit. This core dimerizes to form the PolIII complex. PolIII associates with the gamma complex (composed of gamma, delta, delta prime, psi and chi chains) and with the beta chain to form the complete DNA polymerase III complex. Additionally, DNA helicase (hexamer), DNA primase (monomer), and DNA beta clamp (dimer) were added. The theta subunit (holE) is missing (`'Q0KD75': 2, 'Q0K8W5': 2, 'Q0K937': 3, 'Q0K709': 1, 'Q0KBB9': 1, 'Q0K7F6': 1, 'Q0K9E9': 6, 'Q0K866': 1, 'Q0KFR7': 2`). Source: Uniprot.

### Step 3: Other constraints

Several additional constraints were added. To automatically generate the final model, run:

```
python3 generate_model.py
```

#### Maintenance ATP

Growth- and non-growth-associated maintenance in minimal medium were determined by Park et al., 2011, as 15.3 mmol gDCW<sup>-1</sup> and 3.0 mmol gDCW<sup>-1</sup> h<sup>-1</sup>, respectively. The growth associated maintenance was deemed too low and set to 150 mmol gDCW<sub>-1</sub>.

#### k_app

The model can be calibrated by adding `k_app`, the apparent catalytic rate, for each enzyme (also termed 'enzyme efficiency' in RBA). `k_app` was estimated following the procedure and scripts from the original `RBApy` publication and the accompanying [github repository](https://github.com/SysBioInra/RBApy). The required input were flux boundaries obtained from flux sampling analysis (FSA), enzyme abundance in mmol gDCW<sup>-1</sup>, and the GSM/RBA models. It performs `k_app` estimation by dividing apparent flux by enzyme abundance. The input parameters and final results for `k_app` estimation are detailed in the R notebook [Ralstonia model constraints](https://m-jahn.github.io/projects/).

#### Total protein pool

The total protein pool in mmol gDCW<sup>-1</sup> was estimated based on the publication by Park et al, 2011. They reported an estimated protein concentration for _R. eutropha_ of 0.68 g/gDCW. For comparison, cyanobacteria's protein concentration was estimated with 0.65 g/gDCW. Assuming an average molecular weight per amino acid of 110 g/mol, total protein mass was calculated as:

`c = 0.68 g/gDCW / 110 g/mol * 1000 = 6.1818 mmol/gDCW`

#### Protein fraction per compartment

Protein fraction per compartment was calculated as described in the R notebook [Ralstonia model constraints](https://m-jahn.github.io/R-notebooks/Ralstonia_model_constraints.nb.html). Using proteomics data with annotated protein localization as input, the following growth rate dependent linear models were obtained.

- Fraction of cytoplasmic proteins: `0.8684 + 0.1060 * µ`
- Fraction cytoplasmic membrane proteins: `0.1316 - 0.1060 * µ`

#### Non-enzymatic protein fraction per compartment

Similarly to the above estimation, the non-enzymatic (NE) protein fraction per compartment was determined from proteomics data annotated with gene-reaction associations from the RBA model [Ralstonia model constraints](https://m-jahn.github.io/R-notebooks/Ralstonia_model_constraints.nb.html). 

- Fraction of NE proteins in cytoplasm: `0.5374 - 0.5657 * µ`
- Fraction of NE proteins in cytoplasmic membrane: `0.8414 - 0.2147 * µ`

### Step 4: Solve model

The model can be solved for different environmental conditions by running:

```
python3 solve_rba_model.py .
```
