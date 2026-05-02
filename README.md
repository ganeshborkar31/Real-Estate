# Real Estate Platform - Flat Rent & Sell

A modern, scalable digital platform for buying, selling, and renting residential flats with seamless integration between property listings, user management, and transaction workflows.

---

## 📌 Business Overview

**RealEstate Platform** is a comprehensive solution for flat rental and sales transactions in the residential real estate market. We provide property owners, tenants, buyers, sellers, and brokers with a centralized digital marketplace to:

- **List & Manage** residential properties (flats for rent/sale)
- **Discover Properties** through advanced search and filtering
- **Facilitate Transactions** from listing to closure
- **Manage User Profiles** for buyers, sellers, renters, and brokers
- **Track Leads** and manage inquiries efficiently
- **Enable Secure Bookings** with verification and payment processing

---

## 🎯 Key Business Features

### For Property Owners & Sellers
- **Easy Listing Creation** - Upload photos, documents, and property details in minutes
- **Tenant/Buyer Screening** - Pre-qualified leads with background verification
- **Rental Management** - Track tenants, rent payments, and maintenance requests
- **Multi-Property Management** - Manage portfolios with bulk operations
- **Analytics Dashboard** - View inquiries, response rates, and conversion metrics

### For Renters & Buyers
- **Property Search** - Filter by location, price, amenities, size
- **Neighborhood Insights** - School ratings, transportation, safety scores
- **Verified Listings** - All properties verified by platform
- **Virtual Tours** - 360° photos and video walkthroughs
- **Saved Properties** - Wishlist management and price alerts
- **Comparison Tools** - Side-by-side property comparisons

### For Brokers & Agents
- **Broker Dashboard** - Track owned and managed listings
- **Lead Management** - Centralized inquiry pipeline
- **Commission Tracking** - Automated payment calculations
- **Marketing Tools** - Featured listings and promotional access
- **Performance Analytics** - Success rates and revenue metrics

---

## 💡 Business Value Proposition

| Stakeholder | Value |
|---|---|
| **Property Owners** | Faster sales/rentals with pre-qualified buyers; Transparent fee structure; Reduced vacancy periods |
| **Tenants/Buyers** | One-stop marketplace for verified properties; Secure booking process; Transparent pricing |
| **Brokers** | Higher visibility and lead volume; Reduced paperwork; Commission automation |
| **Platform** | Scalable marketplace model; Transaction-based revenue; High retention through trust & efficiency |

---

## 🏢 Target Market

**Phase 1 - Residential Flats**
- Studio to 4BHK apartments
- Rental duration: 6 months to unlimited
- Sale transactions: New and resale properties
- Price range: Entry-level to premium segments

**Future Expansion**
- Plots and land sales
- Commercial office spaces
- Builder partnerships
- Property finance integration

---

## 🏗️ Platform Architecture

### Tech Stack
- **Backend**: Python 3.11 + FastAPI (high-performance APIs)
- **Database**: PostgreSQL 16 (ACID compliance, scalability)
- **Caching**: Redis 7 (fast queries, session management)
- **Migrations**: Alembic (safe schema updates)
- **Monitoring**: Prometheus + Grafana + Loki (production reliability)
- **Deployment**: Docker Compose (containerized, cloud-ready)
- **Optional Integrations**: Supabase, Pinecone (search & recommendations)

### Directory Structure (Standard Pattern)

```text
real-estate-starter/
├─ app/
│  ├─ api/
│  │  ├─ health.py
│  │  ├─ router.py
│  │  └─ v1/
│  │     ├─ router.py
│  │     └─ endpoints/
│  │        └─ users.py
│  ├─ core/
│  │  └─ config.py
│  ├─ db/
│  │  ├─ base.py
│  │  └─ session.py
│  ├─ features/
│  │  └─ users/
│  │     ├─ models.py
│  │     ├─ schemas.py
│  │     ├─ repository.py
│  │     └─ service.py
│  └─ main.py
├─ alembic/
│  ├─ env.py
│  └─ versions/
├─ monitoring/
│  ├─ prometheus.yml
│  └─ promtail.yml
├─ docker/
│  └─ Dockerfile
├─ docker-compose.yml
├─ alembic.ini
├─ .env.example
├─ requirements.txt
└─ pyproject.toml
```text
real-estate-platform/
├─ app/                          # Application code
│  ├─ api/
│  │  ├─ health.py              # Health & monitoring
│  │  ├─ router.py              # Main API router
│  │  └─ v1/
│  │     ├─ router.py           # v1 API routes
│  │     └─ endpoints/
│  │        ├─ users.py         # User profile endpoints
│  │        ├─ properties.py    # Property listing endpoints (planned)
│  │        └─ bookings.py      # Booking/inquiry endpoints (planned)
│  │
│  ├─ features/                 # Business domain features
│  │  ├─ users/
│  │  │  ├─ models.py           # DB schema
│  │  │  ├─ schemas.py          # API validation schemas
│  │  │  ├─ repository.py       # DB queries
│  │  │  └─ service.py          # Business logic
│  │  │
│  │  ├─ properties/            # Property listings (planned)
│  │  ├─ flat_rent/             # Rental logic (planned)
│  │  ├─ flat_sale/             # Sales logic (planned)
│  │  └─ bookings/              # Transaction workflow (planned)
│  │
│  ├─ core/
│  │  ├─ config.py              # Environment & settings
│  │  └─ security.py            # Auth & verification
│  │
│  ├─ db/
│  │  ├─ base.py                # SQLAlchemy setup
│  │  └─ session.py             # DB connection pool
│  │
│  └─ main.py                   # App entry point
│
├─ alembic/                     # Database migration scripts
├─ monitoring/                  # Prometheus, Grafana, Loki config
├─ docker/                      # Docker image definitions
├─ docker-compose.yml           # Local dev environment
├─ pyproject.toml              # Python dependencies
├─ requirements.txt            # Production dependencies
└─ README.md
```

---

## 📊 Data Architecture Overview

```
User Layer
├─ Buyer/Seller Profile
├─ Tenant Profile  
├─ Broker Profile
└─ Verification Status

Property Layer
├─ Basic Details (Address, Type, Size)
├─ Media (Photos, Videos, Documents)
├─ Pricing & Terms
└─ Availability Status

Transaction Layer
├─ Inquiries/Leads
├─ Bookings
├─ Payments
└─ Audit Trail
```

---

## 🎬 API Request Flow

1. **Client Request** → API Endpoint (`app/api/v1/endpoints/`)
2. **Validation** → Schema validation (`schemas.py`)
3. **Business Logic** → Service layer (`service.py`)
4. **Data Access** → Repository layer (`repository.py`)
5. **Database** → PostgreSQL
6. **Response** → Serialized JSON response

**Why this design?**
- Clear separation makes features scalable
- Business rules centralized & testable
- Easy to add new features following template
- Enables team collaboration without conflicts

---

## 🔐 API Versioning

- Current API: `/api/v1/`
- Strategy: Maintain backward compatibility
- Breaking changes → new version (`/api/v2/`)
- Old versions sunset after 12-month notice

---

## 🚀 Development Setup & Getting Started

### Prerequisites
- Docker & Docker Compose (Recommended)
- OR: Python 3.11+, PostgreSQL 16, Redis 7

### Quick Start with Docker

```bash
git clone <repo-url>
cd real-estate
cp .env.example .env
docker compose up --build
```

**Services Running:**
- **API** - FastAPI backend at `http://localhost:8000`
- **Database** - PostgreSQL 16
- **Cache** - Redis 7
- **Monitoring** - Prometheus, Grafana, Loki
- **Migration** - Alembic schema updates

**Access Points:**
- 📖 API Docs: http://localhost:8000/docs
- 🏥 Health Check: http://localhost:8000/api/v1/health/
- 📈 Prometheus: http://localhost:9090
- 📊 Grafana: http://localhost:3000 (admin/admin)

### Running Without Docker

**Using uv (Fast):**
```bash
uv venv
source .venv/bin/activate
uv sync
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Using pip:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

Create `.env` file (copy from `.env.example`):
```bash
# Database
ASYNC_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/real_estate
SYNC_DATABASE_URL=postgresql://user:password@localhost:5432/real_estate

# Cache
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional Services
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
```

---

## 📝 Database Migrations

### Creating a Migration
```bash
# After modifying models.py
docker compose run --rm migrate alembic revision --autogenerate -m "add properties table"
```

### Applying Migrations
```bash
docker compose run --rm migrate alembic upgrade head
```

### Best Practices
- One logical change per migration
- Review generated SQL before deployment
- Never edit applied migrations in shared environments
- Test migrations locally first

---

## 🏗️ Adding New Features

### Template: Add a New Property Type

Example: Create a "Plot Sale" feature

**Step 1: Create feature folder**
```bash
mkdir app/features/plot_sale
touch app/features/plot_sale/__init__.py
```

**Step 2: Create feature files**
- `models.py` - Database schema
- `schemas.py` - Request/response validation
- `repository.py` - Database queries
- `service.py` - Business rules & calculations

**Step 3: Create API endpoint**
- `app/api/v1/endpoints/plot_sale.py`

**Step 4: Register in router**
- Add import & route in `app/api/v1/router.py`

---

## 📊 Current API Endpoints

### Users API (Examples)
```
POST   /api/v1/users/              - Register new user
GET    /api/v1/users/              - List all users (admin)
GET    /api/v1/users/{user_id}     - Get user profile
PATCH  /api/v1/users/{user_id}     - Update profile
DELETE /api/v1/users/{user_id}     - Deactivate account
```

### Planned Endpoints (Roadmap)
```
POST   /api/v1/properties/         - List new property
GET    /api/v1/properties/         - Search properties
GET    /api/v1/properties/{id}     - Get property details
POST   /api/v1/bookings/           - Create booking/inquiry
GET    /api/v1/bookings/           - Booking history
POST   /api/v1/transactions/       - Payment processing
```

---

## 📈 Monitoring & Performance

The platform includes production monitoring:

- **Prometheus** - Metrics collection
- **Grafana** - Dashboard visualization  
- **Loki** - Log aggregation
- **Promtail** - Log shipping

### Key Metrics Tracked
- API response times
- Database query performance
- Cache hit rates
- Transaction completion rates
- User registration & conversion funnels

---

## 🐛 Troubleshooting

### Issue: Docker port conflicts
**Solution:** Update `docker-compose.yml` port mappings or check for running services
```bash
lsof -i :8000  # Find process using port 8000
docker compose down  # Stop all containers
```

### Issue: Database connection errors
**Solution:** Verify credentials in `.env` and ensure PostgreSQL container is healthy
```bash
docker compose ps
docker compose logs postgres
```

### Issue: Migration failures
**Solution:** Check model imports and review generated SQL
```bash
docker compose run --rm migrate alembic current
```
**Strict dev rule (non-negotiable):** Every time you touch models.py, run:
  ```
    docker compose run --rm migrate alembic revision --autogenerate -m "describe change"
    docker compose run --rm migrate alembic upgrade head
  ```

---

## 📚 Next Steps for Developers

1. **Review** the directory structure and naming conventions
2. **Explore** existing features in `app/features/users/`
3. **Run** the application locally
4. **Create** your first feature following the template
5. **Test** using API docs at http://localhost:8000/docs
6. **Deploy** using Docker to production environment

---

## 🤝 Contributing Guidelines

- Follow feature-based folder structure
- Keep services single-responsibility
- Add validation in schemas.py, not endpoints
- Write tests for business logic
- Document complex business rules
- Use migration files for schema changes

---

## 📄 License

[Add your license here]

---

## 📧 Support & Contact

For questions or issues:
- Create GitHub issue
- Contact development team
- Check documentation in `/docs`
- Install dependencies from `requirements.txt` or run `uv sync`.

## 💼 Team Collaboration Workflow

1. **Plan** feature requirements with product team
2. **Branch** create feature branch for each domain
3. **Implement** using feature template structure
4. **Test** verify endpoints in `/docs` UI
5. **Review** migration scripts and business logic
6. **Deploy** via Docker to staging, then production

---

## 🔮 Future Enhancements

- **Authentication**: JWT-based user authentication & sessions
- **Permissions**: Role-based access control (RBAC)
- **Advanced Features**:
  - Property analytics & insights
  - Smart lead recommendations
  - Automated matching (buyer-property)
  - Background jobs & task queues
- **Quality**:
  - Comprehensive test suite (unit + integration)
  - CI/CD pipeline & automated checks
  - Performance benchmarks & optimization
- **Integrations**:
  - Payment gateways (Razorpay, Stripe)
  - SMS/Email notifications
  - Third-party property feeds
  - Map & location services

---

**Last Updated:** May 2, 2026  
**Maintained By:** Real Estate Platform Team
