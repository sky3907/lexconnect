# seed_lawyers.py - FIXED VERSION
from database import init_db, get_db, User, LawyerProfile, UserRole
from sqlalchemy.orm import Session

def seed_lawyers():
    # CREATE TABLES FIRST
    print("🔨 Creating database tables...")
    init_db()
    
    db_gen = get_db()
    db: Session = next(db_gen)
    
    lawyers_data = [
        ("Rajesh Kumar", "property law, real estate", "Gurgaon", 12, 4),
        ("Priya Sharma", "family law, divorce", "Faridabad", 8, 5),
        ("Amit Singh", "contract law, construction", "Panipat", 10, 4),
        ("Neha Gupta", "property disputes", "Hisar", 6, 4),
        ("Vikram Yadav", "matrimonial law", "Rohtak", 15, 5),
        ("Anita Rao", "commercial contracts", "Sonipat", 7, 3),
        ("Suresh Patel", "land law", "Jhajjar", 9, 4),
        ("Meera Joshi", "family custody", "Bhiwani", 11, 5),
    ]
    
    seeded_count = 0
    for name, spec, city, exp, rating in lawyers_data:
        # Check if user exists
        user = db.query(User).filter(User.name == name).first()
        if not user:
            user = User(
                email=f"{name.lower().replace(' ', '.')}@lawyer.com",
                name=name,
                password_hash="dummyhash",
                role=UserRole.lawyer
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Created lawyer: {name}")
        
        # Add lawyer profile
        profile = db.query(LawyerProfile).filter(LawyerProfile.user_id == user.id).first()
        if not profile:
            profile = LawyerProfile(
                user_id=user.id,
                specialization=spec,
                city=city,
                experience_years=exp,
                rating=rating,
                is_available=1
            )
            db.add(profile)
            db.commit()
            seeded_count += 1
    
    print(f"🎉 Seeded {seeded_count} new lawyers!")
    print("📊 Total lawyers:", db.query(LawyerProfile).count())
    db.close()

if __name__ == "__main__":
    seed_lawyers()
