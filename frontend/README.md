# Frontend Application

## Overview
This is the Next.js frontend for the BiasLens project. It provides the user interface for analyzing text for bias, interacting with the backend API, and displaying the results.

## Getting Started

### Prerequisites
- Node.js (version 18.x or later recommended)
- pnpm (or npm/yarn, though pnpm is preferred for this project)

### Installation
1. Navigate to the `frontend` directory (if you are not already there):
   ```bash
   cd frontend
   ```
2. Install the project dependencies using pnpm:
   ```bash
   pnpm install
   ```
   If you prefer npm or yarn, you can use:
   ```bash
   npm install
   ```
   or
   ```bash
   yarn install
   ```
   (Note: A `pnpm-lock.yaml` is present, so `pnpm install` is the recommended command for consistency.)

### Running the Development Server
Once the dependencies are installed, you can start the Next.js development server:
```bash
pnpm run dev
```
This command will typically start the application on `http://localhost:3000`.

## Accessing the Application
Open your web browser and navigate to:
[http://localhost:3000](http://localhost:3000)

You should see the BiasLens frontend application.

## Project Structure
- **`app/`**: Contains the core application routes, pages, and layouts (using Next.js App Router).
- **`components/`**: Houses reusable UI components.
- **`public/`**: Stores static assets like images and fonts.
- **`styles/`**: Includes global stylesheets and CSS modules.
- **`lib/`**: Utility functions and libraries specific to the frontend.
- **`contexts/`**: React contexts for managing global state.
- **`hooks/`**: Custom React hooks.
- **`next.config.mjs`**: Configuration file for Next.js.
- **`package.json`**: Lists project dependencies and scripts.
- **`pnpm-lock.yaml`**: PNPM lock file.
- **`tsconfig.json`**: TypeScript configuration.

This README provides the basic steps to get the frontend application up and running. For more details on Next.js, refer to the [official Next.js documentation](https://nextjs.org/docs).
