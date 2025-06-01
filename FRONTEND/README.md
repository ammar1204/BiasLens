# BiasLens Frontend

BiasLens Frontend is a web application designed to help users analyze content and gain insights, with a focus on identifying potential biases. It provides a user-friendly interface for interacting with AI-powered analysis tools and visualizing results on a personal dashboard.

## Key Features

*   **Authentication:** Secure sign-in and sign-up functionality for user account management.
*   **Dashboard:** A personalized dashboard to display user-specific data and analysis results, including charts and visualizations.
*   **Content Analysis:** AI-powered tools to analyze text-based content, providing insights and potentially identifying biases.
*   **Theme Switching:** Ability to switch between light and dark modes for user preference.
*   **Rich User Interface:** Modern and interactive UI with components like forms, dialogs, tables, toast notifications, and a command palette.
*   **Supabase Integration:** Utilizes Supabase for backend services, including database interactions and authentication.

## Technologies Used

*   **Framework:** Next.js (v15)
*   **Language:** TypeScript
*   **Styling:** Tailwind CSS (with `tailwindcss-animate`, `clsx`, `tailwind-merge`)
*   **UI Components:** Shadcn/ui (built on Radix UI primitives), Lucide React (icons)
*   **Forms:** React Hook Form, Zod (for schema validation)
*   **State Management:** React Context API, Next-themes
*   **Backend (BaaS):** Supabase
*   **AI Integration:** AI SDK (@ai-sdk/openai)
*   **Charting:** Recharts
*   **Notifications & UI Elements:** Sonner (toasts), CMDK (command palette), Vaul (drawers), Embla Carousel
*   **Build/Dev Tools:** ESLint, PostCSS, PNPM

## Setup Instructions

Follow these instructions to get the frontend up and running on your local machine.

### Prerequisites

*   **Node.js:** Make sure you have Node.js installed (v18 or later recommended). You can download it from [nodejs.org](https://nodejs.org/).
*   **pnpm:** This project uses `pnpm` as the package manager. If you don't have it, install it globally:
    ```bash
    npm install -g pnpm
    ```

### Environment Variables

This project requires certain environment variables to be set for connecting to backend services like Supabase and PostgreSQL.

  Create a new file named `.env.local` in the `FRONTEND` directory.

    *Note: Obtain these values from your Supabase project settings and PostgreSQL database configuration.*

### Installation

Clone the repository (if you haven't already) and navigate into the `FRONTEND` directory. Then, install the dependencies:

```bash
pnpm install
```

### Running the Development Server

Once the dependencies are installed and your environment variables are set up, you can start the development server:

```bash
pnpm dev
```

This will typically start the application on `http://localhost:3000`.

## Available Scripts

The `package.json` file includes several scripts for managing the application:

*   **`pnpm dev`**: Runs the application in development mode.
*   **`pnpm build`**: Builds the application for production deployment.
*   **`pnpm start`**: Starts the production server (after running `pnpm build`).
*   **`pnpm lint`**: Lints the codebase using ESLint.

---

Happy coding!
