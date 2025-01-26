# OpenGov Frontend

This is the frontend for the OpenGov project, built using [Next.js](https://nextjs.org) and [Tailwind CSS](https://tailwindcss.com). The application provides a user-friendly interface for managing government-related tasks, including user authentication and document uploads.

## Getting Started

To get started with the development of this project, follow the instructions below.

### Prerequisites

Make sure you have the following installed on your machine:

- Node.js (version 14 or later)
- npm (Node Package Manager) or Yarn

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ashiqrahman10/opengov.git
   cd opengov/frontend
   ```

2. Install the dependencies:

   Using npm:

   ```bash
   npm install
   ```

   Or using Yarn:

   ```bash
   yarn install
   ```

### Running the Development Server

To run the development server, use the following command:

bash
npm run dev


Or if you are using Yarn:

bash
yarn dev


Open your browser and navigate to [http://localhost:3000](http://localhost:3000) to see the application in action.

### Project Structure

The project structure is organized as follows:

OpenGov/
├── frontend/
│ ├── app/ # Main application files
│ │ ├── (auth)/ # Authentication-related pages
│ │ │ ├── layout.tsx # Layout for authentication pages
│ │ │ ├── login/ # Login page
│ │ │ │ └── page.tsx
│ │ │ └── register/ # Registration page
│ │ │ └── page.tsx
│ │ ├── components/ # Reusable components
│ │ ├── globals.css # Global styles
│ │ ├── layout.tsx # Main layout for the application
│ │ └── page.tsx # Main landing page
│ ├── public/ # Static assets
│ ├── package.json # Project metadata and dependencies
│ ├── tailwind.config.ts # Tailwind CSS configuration
│ └── next.config.mjs # Next.js configuration
└── README.md # Project documentation



### Learn More

To learn more about Next.js and Tailwind CSS, check out the following resources:

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

### Contributing

Contributions are welcome! If you have suggestions for improvements or find bugs, please open an issue or submit a pull request.

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.