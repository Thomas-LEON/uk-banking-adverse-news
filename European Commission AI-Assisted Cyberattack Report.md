# Research Report: AI-Assisted Cyberattack on the European Commission

## 1. What Happened

### What We Know (Confirmed Facts)
* **Disclosure and Timeline:** On November 19, 2026, European Commission spokesperson Thomas Regnier publicly confirmed that the institution had been hit by a cyberattack involving an Artificial Intelligence (AI) tool. The intrusion was first detected on October 22, 2026, and formally confirmed after an initial investigation on October 26, 2026.
* **Nature of the Incident:** Officials described the event as a "campaign"—meaning a coordinated series of related incidents rather than a single isolated breach—targeting "individual systems" within the Commission.
* **Broader Context:** This marks the Commission's third disclosed cyber incident in 2026, following a breach involving Ivanti software in January and a cloud infrastructure incident in March. Officials have not linked the three events.

### What Is Reported / Hypothesized (Unconfirmed by the Commission)
* **Targeted Applications:** According to reporting by *Politico*, the attackers specifically targeted internal administrative platforms, including **Sysper** (the Commission's Human Resources [HR] platform for payslips and time management), **MyPMO** (the staff medical reimbursement system), and internal translation systems.
* **Use of ARTEX:** While Regnier confirmed an AI tool was used without naming it, *Politico* reported that **CERT-EU** (the Computer Emergency Response Team for the EU institutions, bodies, and agencies) detected the attackers using **ARTEX**—an open-source (publicly accessible code) AI-powered penetration-testing framework (software designed to automatically probe IT systems for security weaknesses).

### What We Don't Know (Unknowns)
* **Attribution:** No specific threat actor, cybercriminal group, or nation-state has been officially identified or blamed.
* **Full Containment:** Regnier declined to confirm whether the attack has completely ended, stating only that "many elements have been contained."

---

## 2. What Is the Impact

### What We Know (Confirmed Facts)
* **Operational Disruption:** As a protective and preventive measure, the Commission temporarily took several internal applications offline. Most of these applications have since been restored.
* **Staff Data & Ransomware Status:** As of November 19, 2026, the Commission stated it has found "no evidence of a data breach affecting Commission staff as a whole," and Regnier stated he was "not aware" of any ransomware (malicious software that locks or steals data to extort payment) demand.

### What Is Reported / Hypothesized
* **Duration and Potential Data Exposure:** *Politico* reported that system disruptions lasted for more than 10 days and that attackers may have compromised significant volumes of personal employee information.

### What We Don't Know (Unknowns)
* **Granular Data Loss:** Because the Commission carefully qualified its statement to say there is no evidence of a breach affecting staff *"as a whole,"* it remains unknown whether smaller subsets of individual records, non-staff data, or institutional communications were exfiltrated (stolen).

### Broader Sector Impact: The Impersonation Risk (Revolut Italy Precedent)
* **Why Institutional Breaches Amplify Impersonation:** When public-sector or regulatory IT environments are targeted—especially with AI tools that automate reconnaissance and craft convincing communications—the risk extends beyond the targeted agency to financial institutions that interact with them.
* **Confirmed Case Study (Revolut Italy, September 2026):** In a stark illustration of regulatory impersonation, Revolut confirmed in September 2026 that it suffered a data breach affecting **680 customers** (including 8 in Italy and 55 in France) without its own IT systems ever being hacked. Attackers compromised a legitimate **PEC** (*Posta Elettronica Certificata*, Italy's legally recognized certified email system for official communications) account belonging to the Italian Interior Ministry's regional office (prefecture) in Reggio Calabria.
* **How the Impersonation Bypassed Controls:** Because the fraudulent data requests came from an authentic government domain and passed **DMARC** (Domain-based Message Authentication, Reporting, and Conformance—a technical email check that verifies a message came from a legitimate domain, though not whether the sender's account was hijacked), Revolut's legal team fulfilled the requests over several months believing they were genuine. Exposed data included names, dates of birth, passport and driving license copies, **KYC** (Know Your Customer—mandatory identity verification) selfies, **IBANs** (International Bank Account Numbers), account statements, and cryptocurrency transaction histories. Revolut refused to pay a ransom and notified regulators, including the UK's **ICO** (Information Commissioner's Office) and **FCA** (Financial Conduct Authority), Lithuania's State Data Protection Inspectorate, and Italy's **ACN** (*Agenzia per la Cybersicurezza Nazionale*, the national cybersecurity agency).

---

## 3. What Is Being Done

### Actions by the European Commission (Confirmed Facts)
* **System Isolation and Hardening:** The Commission took affected applications offline, notified impacted internal teams, and is preventively auditing other internal systems while strengthening overall security controls.
* **Inter-Agency Coordination:** The Commission is working closely with **CERT-EU** on technical remediation and has formally notified the **EDPS** (European Data Protection Supervisor—the independent authority overseeing data protection compliance across EU institutions). The forensic investigation remains ongoing.

### Recommended Internal Actions (Regulatory Communication Controls)
* **Audit Regulatory Communication Channels:** Given both the AI-assisted targeting of EU institutions and the Revolut Italy impersonation breach, we should review our existing communication processes with regulators and public authorities to verify whether exchanges rely on a dedicated **secure channel** rather than standard or certified email alone.
* **Implement Multi-Factor Confirmation:** We should verify whether **multi-factor confirmation** (an out-of-band verification step—such as confirming a request through a pre-established, independently verified phone number, official portal, or secondary contact—rather than relying solely on email domain authentication) is enforced before disclosing sensitive data. Ensuring every regulatory request is independently verified as genuine is essential, as technical email filters cannot detect a hijacked legitimate government mailbox.

---

## 4. Potential Root Cause

### What We Know (Confirmed Context)
* **AI-Accelerated Exploitation:** The Commission confirmed that hackers leveraged an AI tool during the campaign.
* **Recent Threat Intelligence Warnings:** On November 5, 2026—two weeks before the Commission's public disclosure—CERT-EU warned its constituency that threat actors were adopting **ARTEX** to launch faster, more frequent, and more scalable automated attacks. A week prior to the disclosure, the **FBI** (U.S. Federal Bureau of Investigation) similarly warned that cybercriminals and nation-states were prolifically abusing ARTEX against government agencies and critical infrastructure, progressing from initial targeting to **privileged access** (high-level administrative control over a system) in under three hours.

### What Is Hypothesized
* **Abuse of Publicly Available AI Frameworks:** Released in July 2026, ARTEX combines commercial AI models to automate vulnerability discovery and exploitation. Although its original code repository was removed in October 2026 following reports of malicious misuse, **forks** (copied and independently hosted versions of the software) remain publicly available. Security analysts assess that tools like ARTEX lower the technical barrier for attackers, allowing them to rapidly scan and exploit internet-facing applications faster and more cheaply than manual hacking.

### What We Don't Know (Unknowns)
* **Initial Entry Vector:** Officials have not disclosed which specific software vulnerability, misconfiguration, or compromised credential allowed the attackers to gain their initial foothold in the Commission's environment.
* **Specific AI Role:** It is not publicly confirmed whether AI was used strictly for automated vulnerability scanning and exploitation (as with ARTEX), or also for **social engineering** (manipulating people into divulging access or data).

---

## 5. Sources and References

* **SecurityWeek** — *European Commission Confirms AI-Assisted Cyberattack Disrupted Services* (November 20, 2026): https://www.securityweek.com/european-commission-confirms-ai-assisted-cyberattack-disrupted-services/
* **Help Net Security** — *European Commission confirms AI-generated cyberattack disrupted its systems* (November 20, 2026): https://www.helpnetsecurity.com/2026/11/20/european-commission-ai-generated-cyberattack-publicly-available-tool/
* **CSO Online** — *European Commission HR hit by cyber attack* (November 20, 2026): https://www.csoonline.com/article/4251068/european-commission-hr-hit-by-cyber-attack.html
* **Penligent** — *European Commission AI Cyberattack: Facts and Unknowns* (November 20, 2026): https://www.penligent.ai/hackinglabs/european-commission-ai-cyberattack/
* **The Record** — *European Commission confirms cyberattack, says hackers used AI tool* (November 19, 2026): https://therecord.media/european-commission-confirms-cyberattack-using-ai
* **Infosecurity Magazine** — *European Commission Confirms AI-Driven Cyber-Attack Took Systems Offline* (November 19, 2026): https://www.infosecurity-magazine.com/news/commission-ai-attack-systems/
* **Reqport Insights** — *How the Revolut data breach happened* (September 25, 2026): https://reqport.com/en/insights/revolut-data-breach
* **SecurityWeek** — *Revolut Data Breach: 5 Months, 680 High-Profile Accounts, $3M Ransom* (September 17, 2026): https://www.securityweek.com/revolut-data-breach-5-months-680-high-profile-accounts-3m-ransom/
* **CyberOne** — *Revolut Data Breach: How Fake Government Requests Exposed Sensitive Customer Information* (September 15, 2026): https://cyberone.security/news/revolut-data-breach-how-fake-government-requests-exposed-sensitive-customer-information
* **Right-Hand Cybersecurity** — *The Revolut Data Breach Was a People Problem. Here's How to Fix It*: https://right-hand.ai/blog/the-revolut-data-breach-was-a-people-problem-heres-how-to-fix-it/