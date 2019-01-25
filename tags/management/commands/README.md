# TOPMed variable tagging project 
 
## Description 
This data package contains the results of the TOPMed Data Coordinating Center's (DCC's) phenotype tagging project. This project aims to increase the value of dbGaP data from the multiple studies that make up TOPMed, as a part of the NIH Data Commons Pilot Phase Consortium. To achieve this goal, we tagged dbGaP variables with informative labels indicating the phenotype concept represented by each variable. The data package consists of full descriptions of each phenotype tag and the mappings between the dbGaP variables and phenotype tags.  
 
## Contact 
Please let us know how you're using this data package! 
To initiate collaborative work with this data package, or for other questions, contact:
 
Leslie Emery, emeryl@uw.edu
 
Research scientist
 
Genetic Analysis Center & TOPMed Data Coordinating Center
 
Department of Biostatistics, University of Washington
 
 
## File descriptions 
* {tags_dump_file} - latest definition of phenotype tags, as exported from our internal webapp database 
* {tags_dump_dd_file} - data dictionary providing information on each of the elements in the previous file 
* {tagged_variable_file} - tab-delimited text file providing mappings between dbGaP variables and tags 
* {tagged_variable_dd_file} - data dictionary providing information on each of the data columns in the previous file 
 
### Background information 
For more information on the dbGaP data and the organizational structure of TOPMed, be sure to read the [TOPMed DCPPC white paper](https://docs.google.com/document/d/1e77a7dZ9I1FcXHbK-CXkbXmP5xywsw1dePsoxX_E6OM/edit?usp=sharing). In particular, you should read sections VII and VIII for information on dbGaP data and another description of the tagging project.  
 
### The tagging process 
We defined tags for 65 phenotypes prioritized by the NHLBI, TOPMed phenotype working groups, and other stakeholders. Seven large cohort studies (ARIC, CHS, CARDIA, FHS, JHS, MESA, and WHI) received subcontract funding for their data experts to perform tagging. Tagging for remaining studies was performed by members of the DCC phenotype team. The DCC added tagging functionality to a webapp that was already developed for internal use. The webapp allowed easy selection of one or more tags for a dbGaP variable and performed error checking. A mapping between a single dbGaP variable and a single tag will be referred to as a 'tagged variable'. After initial tagging, all tagged variables were checked in a 3-step quality review process: 
1. Initial review by the DCC: confirm or flag for removal 
2. Response by study experts: agree to removal or provide explanation of why a tagged variable should remain 
3. Final decision by the DCC: confirm or remove 
The tagged variables in this data package have all passed this 3-step quality review process. 
 
### Goals 
#### Short-term goals 
* Enable creation of cross-study datasets with similar phenotype variables 
* Enable indexing & searching phenotype variables 
* Assist with identification of phenotype variables for harmonization of data values 
#### Long-term goals 
* Train and evaluate automated methods for classifying phenotype variables (e.g. machine learning/natural language processing) 
* Enable indexing & searching via ontology terms or synonyms 
 
## Caveats 
* We have been updating the tag descriptions and instructions as necessary in response to questions that have arisen during the tagging process. If you observe later discrepancies in tag titles, descriptions, or instructions, this is probably the reason, but the tag_pk won't change.
* The 'age at enrollment/collection' tag includes many variables that don't contain actual age information. We asked study representatives to tag both age variables and variables that could be used to calculate age, for example 'days since exam 1' for a laboratory test. 'Age at enrollment/collection' is intended to be useful for actually finding the variables you want to use, but may present some difficulties for developing automated approaches.
* The 'medication/supplement use' tag has a much broader definition than the other tags, because it would be impractical to ask the study data experts to tag variables for dozens of different kinds of medications. Also, the ways that medication datasets are often collected from study subjects (e.g. recall questionnaires, physical inventories of medication by a study staff member, etc.) make it difficult to distinguish variables for different kinds of medication from one another. Finally, we found that it was difficult to provide clear guidance on differentiating between medication (over-the-counter and/or prescription) and dietary supplements. The two kinds of data are often collected together and the judgement on whether a particular substance is a 'medication' or a 'supplement' can be subjective. This led to us including both in the tag. This may make the 'medication/supplement use' tag difficult to use for developing automated approaches.
* We concentrated our efforts on tagging the variables for the dbGaP version of each study that was released at the time we began the tagging project. During the course of the tagging, at least two studies (ARIC and FHS) released updated dbGaP versions. If a given dbGaP variable is still present in the updated study version, its variable accession (phv) will be the same. However, some variables may be removed in the updated study version, which will result in the new version not containing a variable with the phv in question.
 
 
## Release notes 

{release_notes}
 
## Acknowledgements 
### TOPMed DCC phenotype team 
* Cathy Laurie 
* Leslie Emery 
* Adrienne Stilp 
* Alyna Khan 
* Fei Fei Wang 
* Jai Broome 
### Consultation 
* Susan Redline 
* Susan Heckbert 
### Study representatives: 
* Cathy D’Augustine (FHS) 
* Karen Mutalik (FHS) 
* Nancy Heard-Costa (FHS) 
* Chance Hohensee (WHI) 
* David Vu (MESA) 
* Dongquan Chen (CARDIA) 
* Lucia Juarez (CARDIA) 
* Kim Lawson (ARIC) 
* Laura Raffield (JHS) 
* Tony Wilsdon (CHS) 
 
## Project status 
We are working on updating our tagged variables for updated dbGaP study versions. More tagged variables may be added in the future. We have also mapped our tags to UMLS terms and are working on tracking that information and providing it in future data packages. In the meantime, you can view our mapping of phenotype tags to UMLS terms in [this Google sheet](https://docs.google.com/spreadsheets/d/1zwUp-7dmcotaEAFti7j7d4S-4UoTPEXXGhHxDx3cwmo/edit?usp=sharing).
