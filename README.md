## Football ELT Pipeline

Project showcasing an ELT pipeline using an open football API to periodically update analysis of a Streamlit app.

## Stack

- **Extract / Load**: Python
- **Transform**: dbt
- **Storage**: Neon Postgres DB
- **Frontend Hosting**: Streamlit (WiP) 

## Pipeline Overview

```mermaid
graph LR
    A[OpenLigaDB API] --> B{Extract and Load}
    B --> C[(Bronze: Raw Data Schema)]
    C --> D{dbt}
    D --> E[(Silver: Staging Schema)]
    E --> F{dbt}
    F --> G[(Gold: Gold Schema)]
```
