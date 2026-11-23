# Threat Intelligence Report: Decathlon Data Leak (November 23, 2026)

**Report Date:** November 23, 2026  
**Subject:** Unauthorized publication of customer and home-delivery records attributed to Decathlon  

---

## 1. What Happened

On **Monday, November 23, 2026**, around 3:00 AM CET, a **threat actor** (an individual or group conducting malicious cyber activity) using the pseudonym **`4me1`** published a database attributed to the French sporting goods retailer **Decathlon** on a **cybercrime forum** (an online marketplace or community used to trade or distribute stolen data). The archive was posted for free download rather than offered for sale.

### What We Know (Verified Facts)
* **Independent verification of the archive:** Three French breach-monitoring platforms—**Cyberattaque.org**, **FrenchBreaches**, and **Fuites Infos**—independently obtained and analyzed the leaked files, reporting highly consistent volumes.
* **Archive structure (~147 MB uncompressed):** The leak consists of four readable, internally cross-referenced files:

| File / Dataset | Volume | Key Contents & Notes |
| :--- | :--- | :--- |
| **Customer & Delivery Records** | 163,646 rows | Includes **137,549 distinct email addresses** (Fuites Infos counts ~137,140 distinct clients) and **135,586 distinct phone numbers**, plus names, addresses, and delivery notes. |
| **Order History** | 255,011 lines | Spans **July 2021 to November 21, 2026**. Contains 247,913 completed orders, 6,303 cancelled orders, and 795 orders still in "created" status. |
| **Parcel Tracking** | 843 lines | Contains delivery addresses, warehouses, and tracking numbers; 759 references match entries in the main order file. |
| **Customer Reviews** | 832 entries | Post-delivery reviews and comments matching existing order references. |

* **Deduplication nuance:** The figures do not add up to 419,332 unique victims, as the same individuals and orders appear across multiple files.
* **Link to Decathlon:** More than 22,500 records contain official Decathlon store addresses (including Lyon Part-Dieu, Lyon Grolée-Carnot, Grenoble Centre-Ville, and Annecy-Épagny), likely reflecting in-store pickup or logistics workflows. Order descriptions also match Decathlon's specific services (economy/express delivery, room-of-choice delivery, home assembly, and product pickup).
* **Data freshness & pseudonymization:** The latest records date from **November 21, 2026**—just two days before publication. On orders older than one year, customer names were replaced through **pseudonymization** (a privacy technique that substitutes identifying fields like names with artificial placeholders to limit exposure).
* **Distinct from prior incidents:** Analysts note this leak is separate from the October 2026 third-party incident affecting **TrainMe** (a Decathlon-affiliated service), as well as earlier claims such as an unverified July 2026 dark web listing claiming 160 million records and a May 2024 leak of 6,644 Decathlon Spain employee emails.

### What We Don't Know
* **Exact exfiltration date:** While `4me1` claims to have obtained the database on November 22, 2026, researchers cannot independently verify that date from the files alone.
* **Extraction method:** It is unknown whether the data was extracted during a single **exfiltration** (the unauthorized copying or transfer of data out of a system) or collected gradually over time.

---

## 2. What Is the Impact

### What We Know (Confirmed Exposure)
* **Exposed Personally Identifiable Information (PII)**—data that can directly identify or contact an individual: First and last names (for orders under one year old), email addresses, phone numbers, postal addresses, residence types, and elevator availability.
* **Active Black Friday deliveries exposed:** The order dataset contains **611 deliveries scheduled between November 23 and November 28, 2026** (610 of which were still in "created" status at the time of capture), coinciding directly with Black Friday week (November 27, 2026).
* **Physical privacy details:** More than **4,100 records** include free-text delivery instructions written by customers—such as building access conditions, intercom details, floor numbers, and home presence or absence schedules.

### Hypotheses (Projected Risk Scenarios)
* **High-credibility social engineering:** **Social engineering** (manipulating people into revealing sensitive information or taking unsafe actions by exploiting trust) is the primary downstream risk. Because the data is fresh and includes active delivery details, attackers can craft highly convincing **phishing** (fraudulent emails), **smishing** (fraudulent SMS text messages), or **vishing** (fraudulent phone calls) impersonating Decathlon or a courier. Citing a customer's real order or personal delivery note makes requests for "redelivery fees," banking details, or one-time verification codes far more persuasive.
* **Physical security exposure:** Although rarer, exposed access instructions and absence schedules pose a localized privacy and physical security concern for the subset of customers who entered detailed home-access notes.
* **Regulatory scrutiny:** If confirmed as a breach of personal data affecting European Union residents, the incident falls under the **GDPR** (*General Data Protection Regulation*, the EU's comprehensive data privacy law), which requires organizations to notify regulators within 72 hours of becoming aware of a qualifying breach and can carry administrative fines if inadequate security controls are found.

### What We Don't Know
* **Financial or authentication data:** Based on currently analyzed files, there is no indication that passwords, **password hashes** (scrambled cryptographic representations of passwords), or payment card numbers are included—however, because Decathlon has not released an official forensic scope, it is not yet confirmed whether other systems or datasets were accessed beyond the four published files.
* **Active exploitation:** There is no confirmed reporting yet on whether cybercriminals have already launched widespread phishing or fraud campaigns using this specific dataset.

---

## 3. What Is Being Done

### What We Know
* **Independent monitoring and public advisories:** Cybersecurity researchers and French leak-tracking platforms (Cyberattaque.org, FrenchBreaches, Fuites Infos) have analyzed the dump to assess its authenticity and alert consumers.
* **Recommended consumer mitigations:** Security advisories currently urge potentially affected Decathlon customers to:
  * Treat unsolicited emails, SMS messages, or calls referencing a Decathlon delivery with extreme skepticism, even if they cite accurate personal details.
  * Never share passwords, banking details, or **SMS one-time codes** (temporary verification numbers sent to a phone) via links or incoming calls.
  * Report suspicious activity or seek free victim support through **Cybermalveillance.gouv.fr** (the French government's official public assistance platform for cybercrime victims).

### What We Don't Know
* **Decathlon's official response:** As of November 23, 2026, Decathlon has **not publicly confirmed** the leak or issued an official statement.
* **Containment and regulatory notifications:** It is unknown whether Decathlon or a third-party vendor has identified and closed the entry point, notified the **CNIL** (*Commission Nationale de l'Informatique et des Libertés*, France's independent data protection authority), or begun notifying affected customers.

---

## 4. Potential Root Cause

### What We Know
* **System profile:** Analysis of the file fields (home deliveries, room-of-choice placement, home assembly, warehouse tracking, post-delivery reviews, and 1-year name pseudonymization) indicates the data originated from a **home-delivery management tool** used to handle Decathlon orders.

### Hypotheses (Unconfirmed)
1. **Supply chain / third-party compromise (most commonly cited hypothesis):** A **supply chain attack** (a cyberattack targeting a trusted external vendor or partner to reach a larger organization's data) affecting a logistics carrier, delivery-management software platform, or IT service provider contracted by Decathlon. Because the dataset is narrowly scoped to home-delivery workflows rather than full e-commerce accounts, an external logistics platform is a strong candidate.
2. **Direct compromise of an internal Decathlon logistics module:** Unauthorized access directly into a Decathlon-managed delivery database or **API** (*Application Programming Interface*, a software bridge that lets different applications exchange data).
3. **Access vector possibilities:** In similar retail and logistics leaks, initial access typically occurs via stolen credentials (such as employee or partner logins harvested by **infostealer malware**—malicious software designed to extract saved passwords and session tokens from infected devices), an unpatched software vulnerability, or a misconfigured cloud storage bucket or database. No evidence currently favors one technical vector over another.

### What We Don't Know
* **Compromised entity:** Analysts cannot yet determine whether the data was stolen directly from Decathlon's own infrastructure or from an external IT/logistics partner.
* **Specific vendor or vulnerability:** No specific subcontractor, software product, or technical flaw has been identified or linked to the leak.
* **Attacker attribution:** Beyond the pseudonym `4me1` and the forum post, the actor's identity, tooling, and initial intrusion method remain unknown.

---

## 5. Sources and References

* **Cyberattaque.org** — *"Decathlon : plus de 163 000 fiches clients diffusées par un hacker, des livraisons à venir exposées"* (Published November 23, 2026): Detailed technical breakdown of the four leaked files, record counts, cross-references, and lack of official confirmation. https://www.cyberattaque.org/decathlon-plus-de-163-000-fiches-clients-diffusees-par-un-hacker-des-livraisons-a-venir-exposees/
* **Selectra** — *"Decathlon : un pirate diffuse 163 000 fiches clients, dont des livraisons prévues cette semaine"* (Published November 23, 2026): Coverage of the 3:00 AM forum publication by `4me1`, the 611 upcoming Black Friday week deliveries, order status breakdown, and store address matches. https://selectra.info/telecom/actualites/marche/decathlon-fuite-donnees-clients-2026-livraisons
* **Fuites Infos** — *"Decathlon : fuite de données revendiquée visant 137 140 clients"* (Published November 23, 2026): Independent archive verification, identification of the home-delivery management tool origin, 1-year pseudonymization finding, and consumer protection advice. https://fuitesinfos.fr/article/2026-11-23-decathlon
* **CyPro** — *"Decathlon Data Breach Claim: 160 Million Records Exposed"* (Published July 24, 2026): Background reference on the separate, unverified 160-million-record dark web claim, cited to distinguish today's incident from prior reports. https://cypro.co.uk/insights/cyber-bulletins/decathlon-data-breach-claim-160-million-records-exposed/
* **Cibersafety** — *"Decathlon Spain suffers a cyberattack: In-depth analysis"* (Published June 7, 2024): Historical context on the May 2024 Decathlon Spain employee email leak (6,644 records), cited to distinguish it from the November 2026 leak. https://cibersafety.com/en/Decathlon-suffers-a-cyberattack/