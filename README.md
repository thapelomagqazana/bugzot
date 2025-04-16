
---

# **FastAPI + React (Vite + TypeScript) + PostgreSQL/MongoDB Skeleton**
🚀 **Full-stack FastAPI + React Vite + PostgreSQL/MongoDB skeleton** that follows best practices for backend & frontend development.

## **📌 Features**
✅ **FastAPI Backend** with JWT authentication & user CRUD  
✅ **React Frontend** (Vite + TypeScript)  
✅ **Repository Pattern** (Supports SQL & NoSQL)  
✅ **PostgreSQL or MongoDB** (Switch via env variables)  
✅ **Dockerized** for easy deployment  
✅ **Automated Testing** with `pytest`  
✅ **Swagger API Docs** (`/docs`)  
✅ **CORS Configured**  

---

## **📂 Project Structure**
```
.
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── api/endpoints        # API routes
│   │   ├── core                 # Configurations
│   │   ├── db                   # Database setup
│   │   ├── models               # Database models
│   │   ├── repositories         # Repository pattern (SQL & NoSQL)
│   │   ├── schemas              # Pydantic Schemas
│   │   ├── tests                # Pytest test cases
│   │   ├── deps.py              # Dependency injection
│   │   ├── main.py              # FastAPI entry point
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env
├── frontend/                    # React Vite frontend
│   ├── src/                     # Frontend source
│   ├── public/                  # Static assets
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
├── docker-compose.yml            # Docker Compose for Backend + Frontend + DB
├── README.md
```

---

## **🚀 Getting Started**
### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/thapelomagqazana/fastapi-react-skeleton.git
cd fastapi-react-skeleton
```

---

### **2️⃣ Setup Environment Variables**
Create a `.env` file inside `backend/` with:
```env
# Database Configuration
DB_TYPE=sql   # Change to 'nosql' for MongoDB
SQL_URL=postgresql+psycopg2://skeleton_user:skeleton_pass@localhost:5432/skeleton_db
MONGODB_URL=mongodb://mongodb:27017
MONGODB_NAME=fastapi_db

# JWT Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Config
BACKEND_CORS_ORIGINS=http://localhost:3000
```

For **frontend**, create `frontend/.env`:
```env
VITE_PORT=3000
VITE_API_URL=http://localhost:8000
```

---

### **3️⃣ Run with Docker**
```bash
docker-compose up --build
```
This starts:
- **FastAPI backend** at `http://localhost:8000`
- **React frontend** at `http://localhost:3000`
- **PostgreSQL** or **MongoDB** (based on `DB_TYPE`)

---

## **📡 API Endpoints**
Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

| Method | Endpoint                 | Description               |
|--------|--------------------------|---------------------------|
| `POST` | `/auth/signin`           | Sign in                   |
| `POST` | `/auth/signout`          | Sign out                  |
| `POST` | `/api/users`             | Create user               |
| `GET`  | `/api/users`             | Get all users             |
| `GET`  | `/api/users/{user_id}`   | Get user by ID            |
| `PUT`  | `/api/users/{user_id}`   | Update user               |
| `DELETE` | `/api/users/{user_id}` | Delete user               |

---

## **🛠 Running Servers**
### **📌 Run FastAPI**
1. Setup and install
```bash
cd backend
python3 venv env
source env/bin/activate
pip install -r requirements.txt
```

2. Run server
```bash
chmod +x run.sh
./run.sh
```

or manually:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### **📌 Run React**
```bash
cd frontend
npm install
npm run dev
```

## **🛠 Running Tests**
1. Start the backend server first
```bash
cd backend
pytest tests 
```

---

## **🌍 Deployment**
### **📌 Deploy with Docker**
```bash
docker-compose -f docker-compose.prod.yml up --build
```

---

## **📌 Switching Between SQL & NoSQL**
Modify `.env`:
```env
DB_TYPE=sql   # Use 'nosql' for MongoDB
```

---

## **👨‍💻 Contributing**
1. Fork this repository  
2. Create a new branch (`git checkout -b feature-name`)  
3. Commit changes (`git commit -m "Added feature XYZ"`)  
4. Push to the branch (`git push origin feature-name`)  
5. Open a pull request  

---

## **💡 Next Steps**
🔹 Add **Redis** for caching  
🔹 Implement **Role-Based Access Control (RBAC)**

---

## **📜 License**
This project is licensed under the **MIT License**.

---

🚀 **Happy Coding!** 🎯