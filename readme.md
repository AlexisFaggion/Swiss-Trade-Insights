# Swiss Trade Insights

An end-to-end data analytics project using official Swiss foreign trade data to explore import and export trends, trading partners, product categories, and geographic trade concentration.

**Tech stack:** Python · Azure SQL Database · Power BI

**Pipeline:** opendata.swiss API → Python extraction and profiling → Azure SQL Database → Power BI

## Contents

- [Business Context & Objectives](#business-context--objectives)
- [References](#references)
- [Data Source](#data-source)
- [Project Architecture](#project-architecture)
- [How to Run the Data Pipeline](#how-to-run-the-data-pipeline)
- [Data Engineering Challenges](#data-engineering-challenges)
- [Data Profiling Results](#data-profiling-results)
- [Key Design Decisions](#key-design-decisions)
- [Data Quality Investigation](#data-quality-investigation)
- [Temporal VZ Classification Harmonisation](#temporal-vz-classification-harmonisation)
- [Analytical SQL View](#analytical-sql-view)
- [Power BI Data Model](#power-bi-data-model)
- [DAX Measures](#dax-measures)
- [Power BI Dashboard](#power-bi-dashboard)
- [Analytical Scope and Limitations](#analytical-scope-and-limitations)

## Business Context & Objectives

International trade and global supply chains have experienced significant disruptions in recent years. The COVID-19 pandemic affected production and logistics networks, while the conflict in Ukraine disrupted commodity markets and international trade flows. Maritime security incidents in the Red Sea and Bab el-Mandeb Strait prompted shipping companies to reroute vessels. More recently, disruptions around the Strait of Hormuz in 2026 have highlighted the strategic importance of critical maritime trade corridors.

These developments underscore the importance of monitoring international trade patterns and geographic concentration. Understanding how trade flows are distributed across countries and product categories provides valuable insights into the structure and evolution of international trade.

Against this backdrop, several strategic questions arise when analysing Swiss foreign trade:

- Which countries account for the largest share of Swiss imports and exports?
- How have trade flows evolved over time, particularly during periods of economic and geopolitical disruption?
- Which product categories account for the largest trade values, and where is geographic concentration highest?
- How has Switzerland's trade concentration across partner countries evolved over time?


*Swiss Trade Insights* addresses these questions through an interactive Power BI dashboard using official Swiss merchandise trade statistics covering 1988–2025. The project presents long-term trade trends, major trading partners and geographic trade concentration across harmonised categories.

The project uses national trade statistics rather than company-level procurement or logistics data. While it shows patterns of geographic trade concentration, it does not directly measure individual supplier dependencies, shipping-route risks or the causal impact of specific geopolitical events.


*Interactive dashboard:* [Explore the dashboard](https://swisstradeinsights.ch/)


## References

- Bacrot, C., & Faure, M.-A. (2024, April 17). Red Sea Crisis and implications for trade facilitation in Africa. UNCTAD, Transport and Trade Facilitation Newsletter, No. 101, Article 118. [Read publication](https://unctad.org/news/red-sea-crisis-and-implications-trade-facilitation-africa).

- UNCTAD. (2026, March 10). Strait of Hormuz disruptions: Implications for global trade and development (UNCTAD/OSG/TT/INF/2026/1). [Read publication](https://unctad.org/publication/strait-hormuz-disruptions-implications-global-trade-and-development).

---

## Data Source

The project uses official Swiss foreign trade statistics published by the Federal Office for Customs and Border Security (FOCBS) made available through opendata.swiss.

**Trade dataset:** [FOCBS — Goods: Foreign trade by broad economic category / country](https://opendata.swiss/en/dataset/waren-aussenhandel-nach-verwendungszweck-land/)

Trade observations are retrieved through the opendata.swiss CKAN API using the `VZ_IMPEXP_DEF` resource. The dataset contains monthly imports and exports by partner country and economic-use classification.

**VZ classification reference:** [FOCBS — Goods: Foreign trade - Metadata - Broad economic categories](https://opendata.swiss/en/dataset/waren-aussenhandel-stammdaten-verwendungszweck)

The official file `stm_broadeconomiccategory_2025-11-26.csv` was downloaded separately and used to obtain the English descriptions of the VZ classification categories.

---

## Project Architecture

```text
opendata.swiss (CKAN API)
          |
          v
Python — Data Extraction & Ingestion
          |
          |-- API metadata retrieval
          |-- Streamed ZIP download
          |-- Nested archive handling
          |-- CSV profiling and schema standardisation
          |-- Data type conversion
          |-- Bulk loading into Azure SQL
          |
          v
Azure SQL Database
          |
          |-- Raw staging table (staging.trade_raw)
          |-- Data-quality investigations
          |-- VZ classification harmonisation
          |-- Analytical aggregation
          |-- SQL view (analytics.vw_trade_harmonized)
          |
          v
Power BI
          |
          |-- Power Query transformations
          |-- Star schema (FactTrade, DimCountry, DimVZ, DimDate)
          |-- DAX measures and trade KPIs
          |-- Historical trade trends
          |-- Country and category analysis
          |-- Supplier concentration indicators
          |
          v
Interactive Dashboard
```
---

## How to Run the Data Pipeline

The data pipeline can be reproduced using the Python and SQL scripts provided in this repository.

The original Power BI source file (`.pbix`) is not included. The completed dashboard is available separately for interactive exploration.

### Prerequisites

- Python 3.14.2
- Azure SQL Database with appropriate access permissions
- A SQL editor connected to Azure SQL Database
- The Python dependencies listed in `requirements.txt`

### 1. Install Dependencies

From the project root directory, install the required Python packages:

```bash
python -m pip install -r requirements.txt
```

### 2. Configure the Database Connection

Create an Azure SQL Database and configure its connection settings.

Copy `src/.env.example` to `src/.env` and replace the placeholders with your own database credentials.

### 3. Extract and Profile the Data

Run the extraction script to download the source archive from opendata.swiss:

```bash
python src/01_extract_trade_data.py
```

The archive is saved to `data/raw/VZ_IMPEXP_DEF.zip`.

Then run the profiling script:

```bash
python src/02_profile_trade_data.py
```

This examines the historical and 2025 datasets, including their columns, record counts, year ranges, trade directions and publication statuses.

### 4. Create the Staging Table

Run:

```bash
python src/03_setup_database.py
```

This script connects to Azure SQL and automatically executes `src/01_create_staging_schema.sql` to prepare the staging database structure.

The SQL schema script does not need to be executed separately.

### 5. Load the Data into Azure SQL

Run:

```bash
python src/04_load_trade_data.py
```

The script standardises the source schemas, converts data types and bulk-loads the observations into `staging.trade_raw`.

Loading is managed by source file. Previously completed files are skipped, while partially loaded files are reloaded.

### 6. Execute the Remaining SQL Scripts

Open a SQL editor connected to the same Azure SQL Database.

The following scripts can be executed manually:

| SQL script                            | Purpose                                              |
| ------------------------------------- | ---------------------------------------------------- |
| `02_data_quality_checks.sql`          | Validate the loaded staging data                     |
| `03_vz_granularity_investigation.sql` | Investigate VZ classification granularity (optional) |
| `04_create_analytical_view.sql`       | Create the harmonised analytical view (required)     |

The final script creates `analytics.vw_trade_harmonized`, which serves as the data source for the Power BI dashboard.

### 7. Verify the Results

For the original dataset snapshot used in this project, the expected row counts are:

| SQL object                      |      Rows |
| ------------------------------- | --------: |
| `staging.trade_raw`             | 5,761,429 |
| `analytics.vw_trade_harmonized` | 5,529,971 |

The analytical view contains fewer rows because observations are aggregated at the harmonised classification level.

These counts can be checked using:

```sql
SELECT COUNT(*) FROM staging.trade_raw;

SELECT COUNT(*) FROM analytics.vw_trade_harmonized;
```

### Reproducibility Notes

- The source archive is downloaded from opendata.swiss and is not stored in this repository.
- The ingestion script uses expected record counts and file structures corresponding to the original dataset snapshot. Updated source files may require configuration changes.
- The Power BI report and its underlying reference tables are not included in the public repository. Only the Python/SQL data pipeline is provided for reproduction.

---

## Data Engineering Challenges

### Resource Identification

The opendata.swiss CKAN API provides multiple resources, including definitive and provisional trade datasets.

Rather than selecting a resource by its position in the API response, the extraction script identifies it by name:

```python
RESOURCE_NAME = "VZ_IMPEXP_DEF"
```

The script handles resource names stored as either strings or multilingual dictionaries. This avoids relying on the order of resources returned by the API.

### Nextcloud Download Links

The dataset metadata provided a public Nextcloud sharing link. Although the initial request returned HTTP `200`, the response contained an HTML sharing page rather than the expected ZIP archive.

The script resolves this by appending `/download` to the sharing URL.

Downloads are saved to a temporary `.part` file and validated with `zipfile.is_zipfile()` before being renamed to their final filename.

This prevents an HTML page or an incomplete, unrecognisable ZIP download from being treated as a valid archive.

The ZIP check does not verify the integrity of every archived file. Existing local archives are also reused without checking for newer versions.

### Large-File Processing

The definitive source archive is approximately 387 MB, with significantly larger CSV files once decompressed.

To avoid loading the entire HTTP response into memory, the extraction script downloads the archive in 1 MiB chunks using `requests` streaming.

The profiling script also processes CSV files incrementally:

```python
pd.read_csv(csv_file, chunksize=100_000)
```

This allows the pipeline to profile millions of observations without loading the complete CSV into a single DataFrame.

The profiling covers record counts, year ranges, trade directions and publication statuses.

### Nested ZIP Archives

The downloaded archive contains multiple nested ZIP files, organised by trade direction and language.

The historical French datasets are approximately:

- Imports: 298 MiB uncompressed
- Exports: 462 MiB uncompressed

The profiling script opens selected nested archives directly using `zipfile` and `BytesIO`, without extracting intermediate files to disk.

```python
with outer_archive.open(inner_zip_name) as inner_file:
    inner_zip_bytes = BytesIO(inner_file.read())
```

Each inner ZIP is loaded entirely into memory, while pandas processes its CSV contents in chunks.

This avoids unnecessary disk extraction, although the compressed inner archive must still fit in RAM.

### Character Encoding

The historical French CSV files initially produced a `UnicodeDecodeError` when read using UTF-8.

The files use Windows-1252 (`cp1252`) encoding, which supports accented characters found in the French source data.

The parsing configuration therefore specifies:

```python
pd.read_csv(
    csv_file,
    sep=";",
    encoding="cp1252"
)
```

The 2025 files use `utf-8-sig` and a comma delimiter, handled separately through the source-specific parsing configuration.

This preserves the original text values while allowing the historical and recent datasets to be processed consistently.

### Schema Differences Between Historical and 2025 Data

The historical French datasets and the 2025 files use different column names, delimiters and encodings.

| Historical data  | 2025 data      | Standardised column |
|------------------|----------------|---------------------|
| Direction_trafic | flow           | trade_flow          |
| Année            | year           | year                |
| Trimestre        | quarter        | quarter             |
| Mois             | month          | month               |
| Quantité_kg      | netmass        | net_mass_kg         |
| Valeur_CHF       | value_chf      | value_chf           |
| Etat             | status         | status              |

Partner-country fields also differ between imports and exports:

- Historical data: `Pays_isoAlpha2`
- 2025 imports: `countryoforiginisoalpha2`
- 2025 exports: `countryofdestinationisoalpha2`

The loading script uses separate parsing configurations for each source:

| Source                 | Delimiter | Encoding    |
|------------------------|-----------|-------------|
| Historical French CSVs | `;`       | `cp1252`    |
| 2025 CSVs              | `,`       | `utf-8-sig` |

The source columns are mapped to a common structure before insertion into `staging.trade_raw`. The original CSV files remain unchanged.

### Definitive and Provisional Data

The downloaded files contain two publication statuses:

- **1988–2024:** `def` (definitive)
- **2025:** `prov` (provisional)

Although the 2025 source filenames contain `def`, their records are marked `prov`. The pipeline therefore uses the status recorded in the data rather than inferring it from the filename.

The `status` column is preserved in Azure SQL and in the analytical view, allowing definitive and provisional observations to remain distinguishable.

---

## Data Profiling Results

The four source files contain **5,761,429 trade observations**.

| Dataset            | Period    | Records   | Status      |
|--------------------|-----------|----------:|-------------|
| Historical imports | 1988–2024 | 2,183,779 | Definitive  |
| Historical exports | 1988–2024 | 3,393,571 | Definitive  |
| 2025 imports       | 2025      |    83,489 | Provisional |
| 2025 exports       | 2025      |   100,590 | Provisional |
| **Total**          |           | **5,761,429** |         |

The data contains monthly import and export observations by partner country and economic-use classification.

Available measures include net mass in kilograms and trade values in CHF, EUR and USD.

These observations were loaded into Azure SQL, where further data-quality checks and classification harmonisation were performed.

---

## Key Design Decisions

### Azure SQL Database

Azure SQL Database was selected to gain practical experience with a cloud-based relational database and separate data ingestion from reporting.

Azure SQL Database provides the storage and processing capabilities required for the project's approximately 5.8 million records, including data validation and analytical transformations.

### Preserving Staging Data

The pipeline loads standardised source records into `staging.trade_raw` before performing analytical aggregations.

The staging table retains individual observations, their publication status and source-file information. This allows the original measurements to be investigated and the analytical view to be rebuilt without reloading the source archives.

The analytical transformations are implemented separately in `analytics.vw_trade_harmonized`.

### Classification Codes as Text

VZ classification codes are stored as strings, even when they contain numeric characters.

For example:

```text
01
01.2
01.2.2
01.2.2.07
```

These values represent hierarchical identifiers rather than quantities. Storing them as text preserves leading zeros and their classification structure.

### Missing Country Names in 2025 Data

The historical datasets contain partner-country names, while the 2025 files provide country identifiers without the equivalent name field.

When the name is unavailable, the ingestion pipeline preserves it as `NULL` in `partner_country_name` rather than assigning an unverified value.

Country labels are handled separately in the Power BI country dimension.

### pandas and SQL Data-Type Compatibility

During the initial Azure SQL bulk load, some numeric values caused type mismatches between pandas and the SQL driver.

For example, `value_chf` is stored as `BIGINT` in SQL, but pandas may represent numeric columns containing missing values as floating-point values.

The loading script converts pandas and NumPy values into SQL-compatible Python types before calling `cursor.bulkcopy()`.

This includes native integers for `BIGINT`, `Decimal` objects for SQL decimal columns, strings for text fields and datetime objects for timestamps.

### Decimal Precision

The 2025 files contained numerical values that exceeded the decimal scale originally configured for `net_mass_kg`.

The staging database therefore uses `DECIMAL(38,18)` for net mass, while monetary decimal fields use `DECIMAL(28,12)`.

The Python loading script explicitly converts decimal values to the expected SQL precision before insertion, preventing incompatible values from being passed directly to the bulk-copy driver.

However, pandas may initially parse net mass values as floating-point numbers, potentially causing minor precision loss before conversion to Decimal.

### Restartable Data Loading

The historical datasets contain more than 5.5 million records. During the initial load, an error occurred when processing the 2025 files, after the historical data had already been loaded successfully.

To avoid reloading millions of records, the Python loader was adapted to restart at source-file level.

Before processing each file, the script compares its expected record count with the number already stored in Azure SQL:

- **Complete:** skip the file.
- **Missing:** load the file.
- **Partially loaded:** delete the records associated with that source file and reload it.

This allowed the pipeline to resume after failures without repeating completed loads.

The final staging table contains **5,761,429 records**, matching the combined source-file counts. Row-count validation confirms the expected volume, although it does not independently verify every record's contents.

---

## Data Quality Investigation

Data-quality checks were performed in Azure SQL after loading the four source files into `staging.trade_raw`.

### Repeated VZ Combinations

Several records shared the same reporting period, trading partner and VZ classification but contained different trade measures.

For example, three historical US import records from June 2002 shared the VZ4 code `03.1.5.01`:

| Net mass (kg) | Value (CHF) |
|--------------:|------------:|
|         6,067 |     592,309 |
|         6,323 |   4,622,052 |
|        55,832 |  14,146,154 |
|    **68,222** | **19,360,515** |

These records were retained rather than removed as duplicates, since doing so could have discarded legitimate trade values.

The investigation informed the subsequent decision to aggregate records at a harmonised VZ classification level while retaining the individual source observations.

### Namibia ISO2 Code

A data-quality check identified **9,442 records** with a missing `partner_country_iso2` value. All affected observations referred to Namibia, whose ISO2 code is `NA`.

By default, pandas `read_csv()` interprets `"NA"` as a missing-value marker.

The ingestion configuration was corrected:

```python
keep_default_na=False,
na_values=[""],
```

This preserves the valid country code while treating empty fields as missing values.

The affected records in Azure SQL were corrected, and the validation query confirmed:

```text
missing_country_iso2 = 0
```

---

## Temporal VZ Classification Harmonisation

The investigation identified differences in classification detail between historical observations and the 2025 data.

For example, historical records contain repeated observations under VZ4 code `03.1.5.01`, while the 2025 data includes more detailed VZ5 codes:

```text
03.1.5.01
    ├── 03.1.5.01.01
    ├── 03.1.5.01.02
    └── 03.1.5.01.03
```

For selected categories, the number of repeated historical observations matched the number of VZ5 child codes found in 2025. However, this does not establish a one-to-one correspondence between historical observations and the newer subcategories.

Because VZ5 detail is not consistently comparable across the full period, the analytical view uses **VZ4 as the common classification level**, falling back to VZ3, VZ2 or VZ1 where necessary:

```sql
COALESCE(vz4, vz3, vz2, vz1)
```

Observations are aggregated at the selected classification level rather than deleting repeated records.

The individual source observations remain available in `staging.trade_raw`.

---

## Analytical SQL View

The view `analytics.vw_trade_harmonized` provides the aggregated dataset used by Power BI.

It groups source observations by reporting period, partner country, trade flow, VZ classification and publication status, while retaining the relevant VZ hierarchy.

Net mass and trade values in CHF, EUR and USD are aggregated using `SUM()`.

### Additional Standardisation

Historical and 2025 datasets use different language representations for the business-cycle indicator, including `oui` and `Yes`.

The SQL view standardises these values into a binary field, `is_total_business_cycle`, allowing consistent filtering in Power BI.

### Validation Results

The analytical view was validated against the staging table after implementation.

| Dataset                         | Row count |
|---------------------------------|----------:|
| `staging.trade_raw`             | 5,761,429 |
| `analytics.vw_trade_harmonized` | 5,529,971 |
| **Difference**                  |   231,458 |

The reduction results from aggregating source observations, not from deleting records in the staging table.

A uniqueness check on the tested analytical combination returned:

```text
Repeated analytical combinations: 0
```

## Power BI Data Model

The SQL view `analytics.vw_trade_harmonized` was connected to Power BI using Import mode.

Power Query was used to prepare the data and build a star schema with one fact table and three main dimensions, supplemented by English-language reference tables and supporting tables for dashboard interactions.

### Power Query Structure

The initial model created `DimCountry` and `DimVZ` directly from `FactTrade`. This caused a dependency issue when descriptive columns were removed from the fact table, since the dimension queries still referenced them.

To resolve this, a shared base query was created:

```text
TradeBase
├── FactTrade
├── DimCountry
└── DimVZ
```

`TradeBase` retains the full output of the SQL analytical view, while the three downstream queries apply their own transformations. Loading is disabled for `TradeBase` to avoid storing an unnecessary additional table in the model.

Data types were also checked during preparation. Date components use whole numbers, while country and VZ classification codes remain text to preserve their original identifiers.

### FactTrade

`FactTrade` contains monthly trade observations and the measures required for reporting.

The main fields include:

- Trade flow, year, quarter and month
- Partner-country numeric code
- Harmonised VZ classification
- Business-cycle indicator and publication status
- Net mass and trade values in CHF, EUR and USD

A `month_start_date` field was created from the source year and month to connect monthly observations to the date dimension.

Descriptive country and classification fields were removed from the fact table and retained in their respective dimensions.

No additional deduplication was performed in Power Query, as the analytical aggregation had already been implemented in Azure SQL.

### DimCountry

`DimCountry` contains the partner-country numeric code, ISO2 code and country name.

During model preparation, a relationship error revealed that numeric country code `392` was associated with two ISO2 values:

| Country code | ISO2 | Country |
|---|---|---|
| 392 | TP | Timor oriental |
| 392 | TL | Timor oriental |

These values reflect the historical change from `TP` to `TL` for Timor-Leste.

The dimension was standardised to `TL` and grouped by `partner_country_num`, producing a unique country key for the relationship with `FactTrade`.

English country names were subsequently added using the separately imported `CountryReference` table.

### DimVZ

`DimVZ` contains the classification hierarchy:

- `vz1`
- `vz2`
- `vz3`
- `vz_harmonized`

Duplicate classification combinations were removed to produce one record per harmonised VZ category.

The dimension uses the harmonised classification already defined in the SQL analytical view, without repeating the transformation in Power BI.

### English-Language Reference Enrichment

The project was initially developed for French-language reporting before being adapted to English during development.

The trade files contain VZ classification codes without category descriptions.

The selected historical French trade files contain partner-country names in French. However, the original `VZ_IMPEXP_DEF` archive also includes English-language historical files, which were not used in the ingestion pipeline. The 2025 files provide country identifiers without country names.

To support English-language reporting, two additional reference tables were prepared in Power BI:

- **`VZReference`:** Built from the official FOCBS classification metadata, using the English description columns (`_txt_e`) to map harmonised VZ codes to their corresponding category names.
- **`CountryReference`:** A custom reference table mapping Swiss partner-country identifiers to English country names using ISO2/CLDR-based mappings.

During Power Query preparation, some VZ classification codes were incorrectly interpreted as dates. Setting these columns to Text preserved their original identifiers and ensured correct matching with the reference table.

Two DAX calculated columns using `LOOKUPVALUE()` retrieve the corresponding descriptions:

| Calculated column | Reference table | Matching key |
|---|---|---|
| `DimVZ[VZ Category Name]` | `VZReference` | `vz_harmonized` |
| `DimCountry[Country Name EN]` | `CountryReference` | `partner_country_num` |

This enrichment provides consistent English labels throughout the dashboard while preserving the original classification and country identifiers.

### DimDate

An explicit date table was created using DAX `CALENDARAUTO()`.

It contains calendar dates, years, quarters, month numbers, month labels and year-month identifiers.

This provides a dedicated, customisable calendar for monthly trends and Year-over-Year calculations, rather than relying on Power BI's built-in Auto date/time feature, which generates hidden date tables.

### Star Schema Relationships

The central fact table uses three active one-to-many relationships:

| Dimension | Fact table |
|---|---|
| `DimDate[Date]` | `FactTrade[month_start_date]` |
| `DimCountry[partner_country_num]` | `FactTrade[partner_country_num]` |
| `DimVZ[vz_harmonized]` | `FactTrade[vz_harmonized]` |

Filters flow from the dimensions toward `FactTrade`.

The model also includes the relationship between `DimVZ` and `VZReference`, while `CountryReference` supplies English labels through calculated lookups.

This structure separates descriptive attributes from trade measures, supports consistent filtering and incorporates additional reference data without changing the analytical grain of the fact table.

### Supporting Tables

Two additional tables support dashboard interactions and specialised visualisations:

- **`Import/Export`:** Supports switching between import and export measures on the geographic map.
- **`Scatter Categories`:** Supports category-level calculations and visualisation in the trade value and market concentration scatter plot.

## DAX Measures

The Power BI model uses reusable DAX measures to analyse trade performance, historical growth and geographic concentration.

The measures cover business-cycle trade values, Year-over-Year changes, Compound Annual Growth Rates (CAGR), trading-partner concentration and custom weighted concentration indicators.

### Core Trade Measures

Trade values are calculated in CHF, with separate measures for imports and exports.

```dax
Total Trade CHF =
SUM(FactTrade[value_chf])

Imports CHF =
CALCULATE(
    [Total Trade CHF],
    FactTrade[trade_flow] = "IMP"
)

Exports CHF =
CALCULATE(
    [Total Trade CHF],
    FactTrade[trade_flow] = "EXP"
)

Trade Balance CHF =
[Exports CHF] - [Imports CHF]
```

These base measures can be reused in more specific calculations without repeating the underlying aggregation logic.

### General Trade vs. Business-Cycle Trade

Swiss foreign trade statistics distinguish between two official reporting scopes:

- **General Total (Total 2):** Includes precious metals, gemstones, works of art and antiques.
- **Business-Cycle Total (Total 1):** Excludes these categories to provide a more representative measure of underlying trade developments.

This distinction has been used in Swiss trade statistics since 1978. It was introduced because large and volatile transactions, particularly in precious metals, could distort the interpretation of broader import and export trends.

Gold is the main product excluded from the business-cycle total.

All dashboard visualisations and indicators use business-cycle trade values (Total 1). General trade measures remain available in the model but are not used in the dashboard.

The source indicator was standardised in Azure SQL as `is_total_business_cycle`, allowing Power BI to apply a consistent classification across historical and recent data.

```dax
Imports CHF Conjunctural =
CALCULATE(
    [Imports CHF],
    FactTrade[is_total_business_cycle] = 1
)

Exports CHF Conjunctural =
CALCULATE(
    [Exports CHF],
    FactTrade[is_total_business_cycle] = 1
)

Trade Balance CHF Conjunctural =
[Exports CHF Conjunctural]
    - [Imports CHF Conjunctural]
```

**Official references:**

- [FOCBS — FAQ foreign trade statistics](https://www.bazg.admin.ch/en/swiss-foreign-trade-statistics-faq)

### Historical Growth Measures

Two types of growth measures were implemented to analyse changes in Swiss foreign trade.

**Year-over-Year Growth**

Previous-year measures use `SAMEPERIODLASTYEAR()` with the dedicated `DimDate` table.

For example:

```dax
Imports CHF Conjunctural Previous Year =
CALCULATE(
    [Imports CHF Conjunctural],
    SAMEPERIODLASTYEAR(DimDate[Date])
)

Imports Conjunctural YoY % =
DIVIDE(
    [Imports CHF Conjunctural]
        - [Imports CHF Conjunctural Previous Year],
    [Imports CHF Conjunctural Previous Year]
)
```

Equivalent measures are used for exports.

These calculations compare trade values with the corresponding period of the previous year.

**Compound Annual Growth Rate (CAGR)**

Custom CAGR measures calculate the annualised growth rate of imports and exports between the first and last years of the selected period.

The calculations use `MIN()` and `MAX()` to identify the reporting years, `REMOVEFILTERS(DimDate)` to retrieve their full-year trade values, and `POWER()` to calculate compound annual growth.

This provides a comparable annualised growth indicator across different reporting periods.

### Top 3 Trading Partner Concentration

Two measures assess the geographic concentration of Swiss trade among its three largest partners:

- **Top 3 Supplier Concentration %:** Share of imports originating from the three largest supplier countries.
- **Top 3 Export Concentration %:** Share of exports directed towards the three largest destination markets.

The calculations use `TOPN()` to identify the leading countries by trade value and divide their combined value by the corresponding total across all countries.

`ALL(DimCountry)` and `REMOVEFILTERS(DimCountry)` support country-wide rankings and denominators, while `KEEPFILTERS()` preserves applicable country-filter intersections in the Top 3 value measures.

The Country Exposure dashboard includes a historical line chart comparing import and export concentration from 1988 to 2025.

The leading partners are recalculated for each reporting year. This allows the chart to capture changes in the relative importance and concentration of Switzerland's leading trading partners over time.


### Category-Level Partner Concentration

These measures calculate the share of imports or exports attributed to the largest trading partner within each harmonised VZ category.

For example, if Germany supplies CHF 60 million out of CHF 100 million in category imports, the largest supplier share is 60%.

The measures are used in the category scatter plot and as inputs to the weighted concentration indicators described below.

### Weighted Trade Concentration — Custom Indicators

Two custom DAX indicators were developed to measure geographic concentration while accounting for the economic importance of each VZ category.

**Weighted Supplier Concentration** measures import concentration by combining:

1. Each VZ category's share of total imports.
2. The share of that category's imports originating from its largest supplier country.

**Weighted Export Market Concentration** applies the same methodology to exports, using each category's share of total exports and the share directed towards its largest destination market.

For each category, its share of total trade value is multiplied by its largest partner's share. The weighted contributions are then summed across categories using `SUMX()`.

This approach gives greater importance to economically significant categories rather than treating every category equally.

The measures are used to compare the historical evolution of weighted import and export concentration.

**Methodological limitations:**

- These are custom weighted top-partner concentration indicators, not official Swiss trade indicators or Herfindahl–Hirschman indices.
- They measure geographic concentration at country level, not dependence on individual suppliers or customers.

### Trade Value vs. Market Concentration — Custom Scatter Plot

A custom scatter plot was developed to compare trade value and geographic concentration across harmonised VZ categories.

A calculated table, `Scatter Categories`, was created using `CROSSJOIN()` to generate separate import and export observations for each category.

The table is disconnected from the main star schema.

Three DAX measures support the visualisation:

- **Scatter Trade Value CHF:** Calculates import or export values for the selected VZ category.
- **Scatter Concentration %:** Calculates the largest supplier or destination-market share within the category.
- **Scatter Top Country:** Identifies the leading supplier or export destination using its English country name.

The calculations use `SWITCH()` to distinguish imports from exports and `TREATAS()` to apply category filters from the disconnected scatter table to `DimVZ`.

`TOPN()` and `CONCATENATEX()` are used to identify and display the leading trading partner.

Each point represents a **VZ category and trade direction**, rather than an individual country.

The scatter plot compares:

- **X-axis:** Trade value in CHF.
- **Y-axis:** Largest trading-partner share within the category (%).

This visualisation helps identify economically significant categories where trade is highly concentrated in a single partner country.

### Dynamic Import/Export Selection

A Power BI field parameter was created to allow users to switch between import and export measures on the geographic map.

The parameter uses `NAMEOF()` to reference the corresponding measures dynamically.

This enables users to explore both trade directions within a single map visual, without duplicating the visualisation.

## Power BI Dashboard

The Power BI dashboard provides an interactive analysis of Swiss foreign trade from 1988 to 2025. It is organised into three pages covering overall trade performance, geographic exposure, and product-category concentration.

### Page 1 — Trade Overview

**Swiss Foreign Trade — Business-cycle imports, exports and trade balance in CHF | 1988–2025**

This page provides an overview of Switzerland's foreign trade performance, including trade values, historical growth and trade balance trends.

**Key performance indicators:**
- Imports and exports (CHF)
- Trade balance (CHF)
- Import and export Compound Annual Growth Rates (CAGR)

**Visualisations:**
- Import and export values over time (line chart)
- Year-over-Year changes in imports and exports (line chart)
- Import versus export distribution (donut chart)
- Trade balance over time (line chart)

### Page 2 — Country Exposure

**Country Exposure — Switzerland's trade partners and exposure in CHF | 1988–2025**

This page examines the geographic distribution of Swiss foreign trade and the concentration of imports and exports among the country's largest trading partners.

**Visualisations:**
- Interactive geographic map with an import/export toggle and bubbles sized by trade value in CHF
- Top 10 export destinations by trade value (stacked bar chart)
- Top 10 import origins by trade value (stacked bar chart)
- Top 3 Import and Export Partner Concentration over time (line chart)


### Page 3 — Category Exposure

**Category Exposure — Switzerland's category concentration and exposure in CHF | 1988–2025**

This page examines trade values and geographic concentration across harmonised economic-use (VZ) categories.

**Visualisations:**
- Weighted Trade Concentration by Product Category and Country over time (line chart)
- Imports by product category in CHF (stacked bar chart)
- Exports by product category in CHF (stacked bar chart)
- Trade Value & Market Concentration by Category (scatter plot)

**Weighted Trade Concentration**

The historical line chart compares weighted supplier concentration and weighted export-market concentration over time.

These custom indicators highlight changes in geographic concentration while giving greater importance to economically significant VZ categories.

**Trade Value & Market Concentration**

The scatter plot displays trade value (X-axis) against the largest trading-partner share (Y-axis) for each harmonised VZ category and trade direction.

Orange points represent imports and green points represent exports. The leading partner country is identified for each observation.

### Dashboard Navigation and Interactivity

All three pages share a consistent navigation interface.

- **Page navigation:** Buttons allow users to switch between Trade Overview, Country Exposure and Category Exposure.
- **Synchronised time-range slicer:** Enables consistent selection of the reporting period across the three pages, except for visuals whose slicer interactions have intentionally been disabled.

---

## Analytical Scope and Limitations

The analysis covers merchandise trade recorded in Swiss customs statistics. It does not include trade in services.

All dashboard visualisations and indicators use the official business-cycle trade total (Total 1), which excludes precious metals, gemstones, works of art and antiques. The results therefore differ from Switzerland's general merchandise trade total (Total 2).

The dataset used for the project contains definitive observations for 1988–2024 and provisional records for 2025, according to the publication statuses in the downloaded files. Results for 2025 should therefore be interpreted in the context of that data snapshot.

The VZ classification has been harmonised to a common analytical level for comparisons over time, rather than retaining the finest source classification. This improves comparability but limits the detail available for individual product categories.

### Import Country Attribution

On January 1, 2012, Swiss import statistics switched from the country of production to the country of origin.

This methodological change may affect historical comparisons of import partner shares and geographic concentration, particularly when comparing periods before and after 2012.

**Official references:**

- [FOCBS — Methods - Definitions](https://www.bazg.admin.ch/en/swiss-foreign-trade-statistics-methods-definitions)

### Geographic Concentration and Supply-Chain Risk

The concentration indicators assess the geographic distribution of Swiss trade flows across partner countries, rather than dependencies on individual suppliers or customers.

The custom weighted concentration indicators are analytical measures developed specifically for this project, focusing on the largest trading partner within each product category, weighted by the category's share of total trade value.

The analysis is based on national trade statistics and does not incorporate company-level procurement data, inventory levels, delivery lead times, alternative sourcing options or transportation disruptions.

**Geographic concentration should therefore be interpreted as a measure of trade structure rather than a direct assessment of supply chain risk.**
