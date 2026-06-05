# Project Overview

This project is an Odoo module that integrates with the Chilean "Mercado Público" API. Its main purpose is to fetch public bids (licitaciones), filter them based on user-defined keywords, and store them as records in Odoo. These records can then be reviewed by users and converted into CRM opportunities.

## Main Technologies

*   **Backend:** Python, Odoo Framework
*   **Libraries:**
    *   `requests`: For making HTTP requests to the Mercado Público API.
    *   **`fuzzywuzzy`**: For fuzzy string matching to filter bids.
    *   `google-generativeai`: For AI-powered filtering of bids.

## Project Management

This project's development and refactoring roadmap is tracked in the following document:

*   **`docs/REFACTOR_PLAN.md`**: Detailed roadmap for professionalization, including Odoo Discuss integration, Smart CRM automation, Vector Search (AI), and Web Scraping features.

## Architecture

The module follows a standard Odoo application structure:

*   **`models/`**: Contains the data models for the application.
    *   `mercadopublico_api.py`: An abstract model that encapsulates the logic for interacting with the Mercado Público API. It handles fetching, filtering, and processing of bids.
    *   `mercadopublico_licitacion.py`: The main data model for storing bid information. It includes fields for all relevant data from the API, as well as fields for internal tracking and workflow.
    *   `mercadopublico_licitacion_queue.py`: A model to manage a queue of bids to be processed, allowing for asynchronous processing.
    *   `mercadopublico_config.py`: A model for storing configuration settings, such as the API ticket.
    *   `mercadopublico_filtro.py`: A model for managing the keywords used for filtering bids.
*   **`views/`**: Contains the XML definitions for the user interface, including menus, forms, and list views.
*   **`data/`**: Contains data files that are loaded when the module is installed, such as cron job definitions and initial configuration data.
*   **`controllers/`**: (Currently empty) Would contain controllers for handling web requests if the module had a web interface.
*   **`wizards/`**: Contains models and views for wizards, which are used for interactive user workflows, such as the wizard for discarding a bid.
*   **`security/`**: Contains security definitions, including access control lists.

## Building and Running

This is an Odoo module and should be installed into an Odoo environment.

### Dependencies

*   Odoo modules: `base`, `sale`, `crm`, `project`, `mail`
*   Python libraries: `fuzzywuzzy`

### Installation

1.  Add the `MercadoPublico-Odoo` directory to the `addons_path` of your Odoo configuration.
2.  Restart the Odoo server.
3.  Go to the "Apps" menu in Odoo, search for "Mercado Publico Odoo", and click "Install".

### Running

The module runs as part of the Odoo application. The following cron jobs are configured to run automatically:

*   **`cron_importar_licitaciones`**: Imports new bids from the Mercado Público API daily.
*   **`cron_procesar_cola_licitaciones`**: Processes bids from the queue.
*   **`cron_archivar_licitaciones_expiradas`**: Archives bids that have expired.

## Development Conventions

*   The code follows the standard Odoo development guidelines.
*   The module uses a queue system to process bids asynchronously, which is a good practice for long-running tasks.
*   The API interaction logic is well-structured and includes error handling and retries with exponential backoff.
*   The module includes a sophisticated filtering system using keywords and fuzzy string matching.
