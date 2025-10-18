# MarketCloudSystem
It is a distributed cloud-based system for market information service that publishes verified daily prices and alerts concerning various goods and services.
 
 # **A CLOUD-BASED DISTRIBUTED MARKET INFORMATION SERVICE FOR CAMEROON**
<img width="500" height="333" alt="image" src="https://github.com/user-attachments/assets/84ec3942-41d2-42b4-bd85-27767e036128" />


NGONDI CHRIST ALEX | Distributed Systems and Cloud Computing | 14/10/2025 


 
# **ABSTRACT**

This project presents MarketCloudSystem, a distributed information system that enables daily collection and dissemination of market prices across Cameroon through mobile, SMS, and USSD technologies. The system bridges the information gap between farmers, traders, and consumers who often lack real-time access to price information.

The solution operates as a distributed network of mobile agents and user devices connected to a cloud-based backend hosted on Firebase. The backend of the program is implemented with services like an API gateway, message queue, distributed database, a caching layer, and a notification service that provides responses to clients via SMS. 

The system will be simulated using docker, docker compose and other python micro services. The systems will be tested using different methods like; Unit testing, Integration testing, Functional testing, End-to-End testing, load testing, and Stress testing. This will be done under realistic conditions to ensure the wellbeing of the entire system so as to permit the architecture to support eventual consistency, horizontal scaling, and graceful degradation, making it suitable for deployment in resource-constrained environments. 

 This will then enable different market data collected from different regions are stored and synchronized in real-time. Users can query prices through the mobile app, send an SMS, or dial a USSD code (e.g., *123#) to receive instant responses. The project demonstrates distributed system characteristics such as scalability, concurrency, fault tolerance, and transparency using tools like Flutter, Firebase Fire store, and an API for USSD/SMS integration. Results show efficient synchronization, fast response times, and system resilience. MarketCloudSystem provides a sustainable and inclusive solution for economic transparency and fair trade in Cameroon’s informal markets.
 
This project demonstrates how distributed systems principles can be applied to build inclusive, mobile-first services that empower communities with timely, transparent market information. It contributes to the broader goal of digital equity and agricultural resilience in Cameroon and similar contexts.

 
# **TABLE OF CONTENTS**

1	Abstract

2	Table of Contents

3	Introduction

4	Background / Literature Review

5	System Design / Architecture

6	Implementation

7	Testing and Evaluation

8	Challenges & Limitations

9	Conclusion

10	References

11	Appendices

 
# **INTRODUCTION**

First of all, a distributed system is a network of connected computers that collaborate to provide fast, reliable, and scalable services even if there is a malfunction in the system. 
Actually, I’m going to work on a cloud-based distributed market information service for Cameroon. I decided to implement this system because Africa and Cameroon in particular faces major problems in market information reliability. Farmers, traders and consumers rely mostly on informal sources like word-of-mouth. Given the fact that there is no centralized, real-time, and easily accessible source of market price information in Cameroon, market data is fragmented, and communication infrastructure is unevenly distributed. While urban centers may benefit from internet-based platforms, rural communities rely heavily on basic mobile phones and GSM networks. This results in misinformation, poor price negotiation, and economic inefficiency, especially among rural communities.

This disparity creates a digital divide that affects decision-making, bargaining power, and economic outcomes. Farmers may sell produce at unfavorable prices due to lack of awareness, while customers and traders may incur unnecessary transport costs due to outdated fare information. Moreover, during periods of disruption such as floods, strikes, or fuel shortages, communities lack reliable alert mechanisms. 
Hence, this distributed system will permit consumers, traders, organizations/any company and policymakers to track the price trends, spot inflations of any goods and services in the market. This system is built as a distributed cloud-hosted system with the aim to enable access via mobile app, and SMS, to support real-time updates and notifications, to provide a community service relevant to Cameroon and to ensure data consistency, scalability, and reliability using distributed architecture.

 
# **Background / Literature Review**

**DISTRIBUTED SYSTEMS AND CLOUD COMPUTING CONCEPTS**

Distributed systems are is one which consists of multiple autonomous computers, or nodes, working together over a network to appear as a single coherent system.
Key features include;

•	Nodes: Each computer or device in the system is a node. Nodes communicate over a network.

•	Concurrency: Many users can access data simultaneously.

•	Fault tolerance: The system keeps working even if some parts fail. It uses redundancy and error recovery.

•	Scalability: The system can handle growing amounts of data and users.

 **TYPES OF DISTRIBUTED SYSTEMS**

•	Client-Server: Centralized data server with multiple clients.

•	Peer-to-Peer: Each node both provides and consumes services.

•	Hybrid Cloud-Based Systems: Combines multiple nodes and services hosted in the cloud for flexibility and reliability.

**TOOLS/LANGUAGES USED**

**RELATED SYSTEMS**

•	FAO Food Price Monitoring Tools: Provide global price trends but not local African market data.

•	MFarm (Kenya): It is an SMS-based platform that provides Kenyan farmers with market prices, weather updates, and buyer contacts. It uses a centralized server to process queries and send replies. While effective, M-Farm lacks distributed architecture, making it less resilient to scaling and failures.

•	AgriSense (Nigeria): SMS-based agricultural price reporting system.

 
# **System Design / Architecture**

**SYSTEM OVERVIEW**

The system is a cloud-hosted distributed service that ingests SMS/USSD reports, processes them asynchronously, stores them in a distributed database, and serves queries via cache for low latency.

**ARCHITECTURE DIAGRAM**
 

1. Mobile Node (Flutter App)
   
•	Who uses it: Traders, cooperatives, or market controllers

•	What it does: They open a Flutter-based mobile app and submit price reports (e.g., “Maize at Mfoundi Market = 450 XAF/kg”).

•	How it connects: The app communicates with the backend over the internet (HTTPS API).

•	Why it matters: This ensures that trusted reporters can send structured, authenticated data directly into the system.

2. SMS Node
   
•	Who uses it: Farmers, traders, and households with basic phones.

•	What it does: They send an SMS in a keyword format (e.g., PRICE MAIZE CENTRE).

•	How it connects: The SMS goes through the mobile operator (MTN/Orange/Nextel) or an aggregator, which forwards the message to the backend API.

•	Why it matters: SMS works on any phone, even without internet, making the service inclusive for rural communities.

3. USSD Node
   
•	Who uses it: Any user with a mobile phone (no internet required).

•	What it does: They dial a USSD short code (e.g., *123#) and navigate a menu:

1.	Prices
   
2.	Transport fares
	
3.	Alerts
	
•	How it connects: The operator’s USSD gateway forwards menu selections to the backend API.

•	Why it matters: USSD is interactive, session-based, and very familiar to African users (used for mobile money, airtime, etc.).

4. Cloud Backend
   
•	Stores: All incoming reports and queries are stored in a distributed database (CockroachDB/Postgres).

•	Validates: Worker services clean, reduplicate, and validate incoming data (e.g., reject negative prices, flag anomalies).

•	Synchronizes: Cache ensures fast responses; DB ensures durability.

•	Responds: Sends SMS replies back through the operator, sends USSD menu responses back to the user and confirms submissions in the Flutter app.


🔹 How the Flow Works

1.	Traders submit prices via the Flutter app → Backend stores and validates.
	
2.	Users send SMS queries → Backend looks up prices in cache/DB → Sends SMS reply.
	
3.	Users dial USSD code → Backend serves interactive menus → Sends back menu responses.
	
4.	Backend synchronizes everything so that whether data comes from Mobile, SMS, or USSD, it’s consistent and up to date.
	
🔹Distributed System Characteristics in the Diagram

•	Multiple entry points: Mobile, SMS, and USSD all connect to the same backend.

•	Scalability: Each channel (API, workers, DB, cache) can be scaled independently.

•	Fault tolerance: If one channel (e.g., SMS) is down, others (USSD, Mobile) still work.

•	Transparency: To users, it feels like one unified service, even though multiple nodes and services are involved.

•	Replication & consistency: Database and cache replicate data across nodes; users may see slight delays (eventual consistency) but the system converges.


 
# **IMPLEMENTATION**

**TOOLS AND FRAMEWORKS**

•	Frontend: Flutter

•	Backend: Firebase Cloud Functions (Python)

•	Database: Firestore (NoSQL, real-time replication)

•	SMS/USSD Gateway: Africa’s Talking 

•	Testing Tools: Android Studio Emulator

 
**TESTING AND EVALUATION**

 
# **CHALLENGES AND LIMITATIONS**



  





  

