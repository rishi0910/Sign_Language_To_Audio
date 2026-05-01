# Sign Language to Audio Website

A web application for converting sign language to audio using real-time video processing.

## Features

- Real-time sign language recognition
- Audio output generation
- User authentication with Google OAuth
- MongoDB database integration

## Prerequisites

- Node.js (v14 or higher)
- MongoDB Atlas account
- Google OAuth credentials

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file with the following variables:
   ```
   PORT=5000
   MONGODB_URI=your_mongodb_uri_here
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   JWT_SECRET=your_jwt_secret
   ```

## Usage

Start the server:
```bash
npm start
```

The application will be available at `http://localhost:5000`

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Express.js, Node.js
- **Database**: MongoDB
- **Authentication**: Passport.js with Google OAuth
- **Security**: JWT, bcryptjs, CORS

## License

ISC
