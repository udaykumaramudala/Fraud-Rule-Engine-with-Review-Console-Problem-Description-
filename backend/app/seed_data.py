from datetime import datetime, timezone, timedelta
from app.database import SessionLocal, Base, engine
from app.models import Transaction, RuleEvaluation, ReviewAudit, NotificationLog
from app.schemas import TransactionCreate
from app.services.transaction_service import transaction_service
from app.services.review_service import review_service

def seed_database(reset: bool = True):
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        print("🌱 Seeding realistic fraud rule engine dataset...")

        # -------------------------------------------------------------
        # Profile 1: Normal Everyday User (USR-1001: Alice Smith)
        # Consistent NYC shopping, moderate amounts ($15 - $120)
        # -------------------------------------------------------------
        alice_txs = [
            TransactionCreate(
                user_id="USR-1001",
                amount=14.50,
                merchant="Starbucks Cafe",
                category="food_and_beverage",
                latitude=40.7580,
                longitude=-73.9855,
                location_name="New York, USA",
                ip_address="198.51.100.12",
                device_id="iphone_15_alice",
                timestamp=now - timedelta(days=2, hours=4)
            ),
            TransactionCreate(
                user_id="USR-1001",
                amount=89.20,
                merchant="Whole Foods Market",
                category="groceries",
                latitude=40.7589,
                longitude=-73.9851,
                location_name="New York, USA",
                ip_address="198.51.100.12",
                device_id="iphone_15_alice",
                timestamp=now - timedelta(days=1, hours=8)
            ),
            TransactionCreate(
                user_id="USR-1001",
                amount=45.00,
                merchant="Uber Ride",
                category="transportation",
                latitude=40.7484,
                longitude=-73.9857,
                location_name="New York, USA",
                ip_address="198.51.100.12",
                device_id="iphone_15_alice",
                timestamp=now - timedelta(hours=3)
            )
        ]
        for tx in alice_txs:
            transaction_service.process_and_create_transaction(db, tx)

        # -------------------------------------------------------------
        # Profile 2: Unusual Amount Fraud (USR-2005: Bob Miller)
        # Normal average ~$50. Suddenly a $9,800 diamond purchase!
        # -------------------------------------------------------------
        bob_history = [
            TransactionCreate(
                user_id="USR-2005",
                amount=42.00,
                merchant="Shell Gas Station",
                category="automotive",
                latitude=34.0522,
                longitude=-118.2437,
                location_name="Los Angeles, USA",
                ip_address="203.0.113.88",
                device_id="pixel_8_bob",
                timestamp=now - timedelta(days=3)
            ),
            TransactionCreate(
                user_id="USR-2005",
                amount=65.50,
                merchant="Target Department Store",
                category="retail",
                latitude=34.0600,
                longitude=-118.2490,
                location_name="Los Angeles, USA",
                ip_address="203.0.113.88",
                device_id="pixel_8_bob",
                timestamp=now - timedelta(days=1, hours=5)
            ),
            TransactionCreate(
                user_id="USR-2005",
                amount=38.90,
                merchant="Chipotle Mexican Grill",
                category="food_and_beverage",
                latitude=34.0510,
                longitude=-118.2410,
                location_name="Los Angeles, USA",
                ip_address="203.0.113.88",
                device_id="pixel_8_bob",
                timestamp=now - timedelta(hours=6)
            ),
        ]
        for tx in bob_history:
            transaction_service.process_and_create_transaction(db, tx)

        # Bob's Anomaly: Massive spike!
        bob_fraud = TransactionCreate(
            user_id="USR-2005",
            amount=9850.00,
            merchant="De Beers Diamond Jewellers",
            category="luxury_goods",
            latitude=34.0700,
            longitude=-118.2600,
            location_name="Beverly Hills, USA",
            ip_address="185.220.101.5",
            device_id="unknown_browser_win",
            timestamp=now - timedelta(minutes=45)
        )
        bob_created = transaction_service.process_and_create_transaction(db, bob_fraud)

        # -------------------------------------------------------------
        # Profile 3: Impossible Travel / Speed Velocity (USR-3010: Carlos Mendoza)
        # Tx 1: Madrid, Spain at 10:00 AM
        # Tx 2: Tokyo, Japan 25 minutes later! (10,700 km apart)
        # -------------------------------------------------------------
        carlos_tx1 = TransactionCreate(
            user_id="USR-3010",
            amount=75.00,
            merchant="El Corte Ingles",
            category="retail",
            latitude=40.4168,
            longitude=-3.7038,
            location_name="Madrid, Spain",
            ip_address="80.24.12.90",
            device_id="samsung_s24_carlos",
            timestamp=now - timedelta(minutes=35)
        )
        transaction_service.process_and_create_transaction(db, carlos_tx1)

        carlos_tx2 = TransactionCreate(
            user_id="USR-3010",
            amount=1450.00,
            merchant="BicCamera Electronics",
            category="electronics",
            latitude=35.6762,
            longitude=139.6503,
            location_name="Tokyo, Japan",
            ip_address="133.242.18.4",
            device_id="unknown_mac_safari",
            timestamp=now - timedelta(minutes=10)
        )
        carlos_created = transaction_service.process_and_create_transaction(db, carlos_tx2)

        # -------------------------------------------------------------
        # Profile 4: Transaction Velocity Attack (USR-4099: David Kim)
        # Automated card testing bot: 4 rapid transactions within 3 minutes
        # -------------------------------------------------------------
        base_time = now - timedelta(minutes=15)
        for i in range(4):
            bot_tx = TransactionCreate(
                user_id="USR-4099",
                amount=2.50 + (i * 1.50),
                merchant=f"Digital Game Key #{i+1}",
                category="digital_goods",
                latitude=51.5074,
                longitude=-0.1278,
                location_name="London, UK",
                ip_address=f"195.154.122.{10+i}",
                device_id="curl_bot_linux",
                timestamp=base_time + timedelta(seconds=i * 35)
            )
            transaction_service.process_and_create_transaction(db, bot_tx)

        # -------------------------------------------------------------
        # Profile 5: High-Risk Category Anomaly (USR-5500: Elena Rostova)
        # -------------------------------------------------------------
        elena_tx = TransactionCreate(
            user_id="USR-5500",
            amount=3200.00,
            merchant="Binance P2P Crypto Desk",
            category="crypto_exchange",
            latitude=48.8566,
            longitude=2.3522,
            location_name="Paris, France",
            ip_address="194.187.249.2",
            device_id="elena_laptop",
            timestamp=now - timedelta(minutes=120)
        )
        elena_created = transaction_service.process_and_create_transaction(db, elena_tx)

        # Simulate reviewer review actions on some past items
        review_service.update_transaction_status(
            db,
            transaction_id=elena_created.transaction_id,
            new_status="CLEARED",
            reviewer="Sarah Jenkins (Senior Compliance)",
            notes="Customer called 2FA support and confirmed authorized crypto purchase."
        )

        print("✅ Seeding successfully completed!")
        print(f"Total transactions: {db.query(Transaction).count()}")
        print(f"Flagged transactions: {db.query(Transaction).filter(Transaction.status == 'FLAGGED').count()}")
        print(f"Notifications logged: {db.query(NotificationLog).count()}")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
