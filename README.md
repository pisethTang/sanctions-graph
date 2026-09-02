# SanctionsGraph
A FinTech compliance intelligence tool that screens education agents and international applicants against global sanctions lists, then visualzies hidden risk connections (shared addresses, phone numbers, banking details) as an interactive graph. 

Project goals:
1. learn more about challenges and solutions in fintech/ed-tech. 
2. have fun -- simplicity 
3. quench my curiosity ... 


```
- "Flywire's own 10-K admits they are under active OFAC investigation for sanctions violations." (Page 28, Item 1A)
- "A Florida school was fined $1.72 million by OFAC for failing to screen tuition payors."
- "The industry false-positive rate is 90–95%, meaning compliance teams drown in noise — my graph approach makes the 'why' visible and auditable."
```


# Key terminologies
1. PEP: 
2. OpenSanctions Data

# Work in progress, TODO: 
- 

# Core engineering concepts
- Preserving traceability from the original record 
- 


# Try it


# Tech stacks
1. Frontend: Vue.js 3 (composition api) deployed on Vercel.
2. Backend: Django (REST framework) deployed on Railway.
3. Database: PostgreSQL,
4. Testing: pytest - backend (unit, integration, e2e)

Both ci and cd workflows were created for both frontend and backend using GitHub Action.


# Building & running 


# References
1. [GitHub CLI](https://github.com/cli/cli?ref_product=cli&ref_type=engagement&ref_style=text#installation)
2. [OFAC Official Website](https://ofac.treasury.gov/)
3. [OFAC Video Series](https://ofac.treasury.gov/ofac-video-series)
4. [Wikipedia](https://en.wikipedia.org/wiki/Office_of_Foreign_Assets_Control)
5. [SDN List](https://en.wikipedia.org/wiki/Specially_Designated_Nationals_and_Blocked_Persons_List)
6. [US Government Sanctions](https://en.wikipedia.org/wiki/United_States_government_sanctions)



| Resource                              | Link                                                                                                              | Why It Matters                                                                                |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **OpenSanctions Docs**                | [opensanctions.org/docs](https://www.opensanctions.org/docs/)                                                     | The API you will use for your project. Covers entity matching, bulk data, and the data model. |
| **OpenSanctions API Tutorial**        | [opensanctions.org/docs/api](https://www.opensanctions.org/docs/api/)                                             | Quickstart for the `/match` endpoint — exactly what you need for screening.                   |
| **OpenSanctions Swagger UI**          | [api.opensanctions.org/docs](https://api.opensanctions.org/docs)                                                  | Interactive API docs to test requests.                                                        |
| **Microsoft OpenSanctions Connector** | [learn.microsoft.com/en-us/connectors/opensanctions](https://learn.microsoft.com/en-us/connectors/opensanctions/) | Shows how enterprises integrate OpenSanctions into Power Automate / Power Apps.               |



7. [13 videos covering OFAC basics, the 50% rule, false positives, and sanctions evasion red flags](https://www.youtube.com/playlist?list=PL0Pufzwcosu-9zpy41pyugHN08aR5OXm-)
8. 

| Article                                                           | Link                                                                                                  | Key Insight                                                                                                     |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **"The Problem of False Positives in AML Screening"**             | [sanctions.io/blog](https://www.sanctions.io/blog/the-problem-of-false-positives-in-aml-screening)    | **90–95% of alerts are false positives.** This is the core pain point your graph-visualization approach solves. |
| **"How to Reduce False Positives in Sanctions Screening"**        | [sardine.ai/blog](https://www.sardine.ai/blog/rules-to-reduce-false-positives-in-sanctions-screening) | Most FIs spend >5–10 min per alert and resolve <10% as true matches.                                            |
| **"Why False Positives No Longer Matter in AML"**                 | [workfusion.com/blog](https://www.workfusion.com/blog/false-positives-do-not-matter-in-aml/)          | Argues that AI should handle the volume, not just tune thresholds. Relevant to your AI-augmented narrative.     |
| **"Sanctions Screening Challenges and Best Practices"**           | [feedzai.com/blog](https://www.feedzai.com/blog/sanctions-screening/)                                 | Explains why sub-second screening and holistic matching (not just names) are now regulator expectations.        |
| **"OFAC Meaning: What Is the Office of Foreign Assets Control?"** | [innreg.com/blog/ofac-meaning](https://www.innreg.com/blog/ofac-meaning)                              | Good primer on penalties: up to **\$377,700 per violation** or twice the transaction value.                     |




| Book                                                                           | Author                         | Why Read It                                                                                                                                                           |
| ------------------------------------------------------------------------------ | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ***The Art of Sanctions: A View from the Field***                              | Richard Nephew                 | Written by the architect of Iran sanctions. Understand the *psychology* of why sanctions exist — makes you a better compliance engineer.                              |
| ***Sanctions Screening: A Key Element of AML and Financial Crime Prevention*** | CA Mayur Joshi & Vedant Sangit | **The most practical book for your project.** 144 pages on how screening systems work, evasion techniques, and how to build a compliance program.                     |
| ***Backfire***                                                                 | Agathe Demarais                | Economist Intelligence Unit perspective on how sanctions evasion works and why overuse of sanctions is creating a multipolar workaround economy.                      |
| ***Mastering Anti-Money Laundering and Counter-Terrorist Financing***          | Tim Parkman                    | Operational guide to AML programs, transaction monitoring, and SARs.                                                                                                  |
| ***Moneyland***                                                                | Oliver Bullough                | Investigative journalism on offshore finance and how oligarchs hide wealth. Builds intuition for why UBO (Ultimate Beneficial Ownership) matters in your graph model. |
| ***Billion Dollar Whale***                                                     | Tom Wright & Bradley Hope      | The 1MDB scandal. Shows how PEPs and intermediaries exploit siloed bank KYC — exactly the network problem your tool addresses.                                        |



10. [RSM](https://github.com/rsms/rsm/tree/main/.logbook)