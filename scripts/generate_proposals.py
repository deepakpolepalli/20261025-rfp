"""Create four 3-page, explicitly fictional RFPs for one common request."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle

PROFILES=[
 {'name':'Apex Systems','file':'apex_systems.pdf','price':245000,'annual':32000,'weeks':16,
  'summary':'Apex proposes a security-led procurement portal with a detailed integration architecture. The higher price funds dedicated technical specialists and controlled rollout.',
  'solution':'The solution uses containerized application services, a PostgreSQL transactional store, and a separate reporting layer. SAML SSO and role-based access protect buyer and supplier workspaces. An API gateway integrates purchase orders and supplier master data with ERP through authenticated REST endpoints. Failed ERP messages enter a retry queue with idempotency keys and an operations dashboard. Capacity tests target 500 concurrent users with 95th percentile response under two seconds.',
  'plan':'Delivery takes 16 weeks: discovery in weeks 1-2, integration design in weeks 3-4, portal build in weeks 5-10, migration and acceptance testing in weeks 11-14, then controlled rollout in weeks 15-16. The team includes a project manager, solution architect, three engineers, one security specialist and one tester. A weekly risk register tracks ERP access, data quality and acceptance dependencies.',
  'security':'Encryption uses TLS 1.3 in transit and AES-256 at rest. Administrators use MFA and least-privilege roles. Audit logs retain user and administrative changes for 365 days. Monthly vulnerability scans and an independent pre-launch penetration test are included. Recovery targets are RPO four hours and RTO eight hours, validated in a restore exercise. Apex states an ISO 27001-aligned control framework; no certification certificate is attached.',
  'support':'Support operates 24x5 with a one-hour response target for priority-one incidents. Quarterly service reviews and an escalation manager are included. The fictional project team describes three comparable procurement deployments. Fictional reference: Harbor Components procurement manager; reference contact verification is not included.'},
 {'name':'BrightPath Tech','file':'brightpath_tech.pdf','price':98000,'annual':12000,'weeks':8,
  'summary':'BrightPath offers the lowest upfront price and an accelerated eight-week rollout using a standard portal template. Security details and comparable-project experience are limited.',
  'solution':'The proposed web portal includes supplier registration, purchase-order reporting and standard role templates. SSO is supported through a third-party identity connector. ERP data initially moves through nightly CSV imports; API integration is a separately estimated enhancement. The proposal expects 100 concurrent users but supplies no load-test acceptance plan.',
  'plan':'Delivery takes eight weeks: requirements and template selection in weeks 1-2, configuration in weeks 3-5, user testing in weeks 6-7 and launch in week 8. A project lead and two generalist developers perform implementation. The customer provides test data and completes acceptance within five business days. A detailed migration reconciliation plan is not provided.',
  'security':'The proposal states that cloud hosting provides standard encryption and password protection. Specific audit retention, certifications, penetration-test scope, recovery targets and privacy-processing terms are not specified. These details are deferred to contracting. A basic backup service is mentioned without restore-test evidence.',
  'support':'Email support is available during business hours with a next-business-day response target. Out-of-hours support is separately priced. The company describes one small website implementation but provides no comparable procurement-system reference. Training consists of one remote two-hour session.'},
 {'name':'NexaWorks','file':'nexaworks.pdf','price':178000,'annual':22000,'weeks':12,
  'summary':'NexaWorks offers a balanced twelve-week delivery with the strongest detailed implementation and support commitments in this fictional fixture set.',
  'solution':'The portal combines modular onboarding workflows, SAML SSO, role-based buyer and supplier views, and reporting dashboards. ERP integration uses documented REST mappings for supplier IDs, purchase orders and status updates, with retry and reconciliation reports. Initial acceptance targets 300 concurrent users with documented load tests. The data model and error-handling runbook are reviewed at the design gate.',
  'plan':'Delivery takes 12 weeks with signed gates: discovery and data profiling in weeks 1-2; design and mapping approval in week 3; two build sprints in weeks 4-7; trial migration and reconciliation in weeks 8-9; user acceptance and role testing in weeks 10-11; cutover and hypercare in week 12. Each gate has an owner, checklist and rollback condition. The team includes a delivery manager, integration lead, two developers, migration analyst and QA lead. A 10-percent schedule contingency covers ERP access delays, with weekly dependency reviews.',
  'security':'The solution specifies TLS encryption, managed database encryption at rest, MFA for administrators, role review before launch and 180-day audit retention. A privacy data-flow inventory and pre-launch vulnerability scan are included. Nightly backups target RPO 24 hours and RTO 12 hours, tested before acceptance. External certification evidence is not attached.',
  'support':'Support includes 24x7 priority-one coverage, a 30-minute acknowledgement target and four-hour workaround target. A named service manager leads monthly reviews. Four weeks of post-launch hypercare, administrator training, runbooks and knowledge transfer are included. The fictional team reports four comparable workflow projects and supplies two fictional reference summaries, Meridian Manufacturing and Elm Logistics.'},
 {'name':'Orbit Digital','file':'orbit_digital.pdf','price':165000,'annual':24000,'weeks':14,
  'summary':'Orbit emphasizes experienced staff and extensive fictional customer references at a medium price, but leaves the ERP integration method vague.',
  'solution':'The supplier portal offers registration workflows, reporting and existing SSO modules. The architecture is described as a proven enterprise platform with scalable hosting. ERP connectivity will be finalized during discovery; interface mappings, retry behaviour and data reconciliation are not specified. The proposal does not provide measurable performance acceptance targets.',
  'plan':'Delivery takes 14 weeks: discovery in weeks 1-3, platform configuration in weeks 4-9, testing in weeks 10-12 and rollout in weeks 13-14. A senior programme manager, platform consultant, two developers and training lead form the team. Milestone reviews occur every two weeks. A high-level risk register is supplied; integration dependencies remain to be assessed.',
  'security':'Orbit specifies encrypted network traffic, encrypted backups, administrator MFA and role-based access. Access logs are retained for 90 days. The team describes annual security reviews and requests a joint privacy workshop. Independent certification, penetration-test acceptance criteria and recovery time objectives are not documented.',
  'support':'The service desk provides 24x5 support with a two-hour priority-one response target and quarterly improvement reviews. The proposed leadership team reports ten years of enterprise implementation experience and eight comparable projects. Three explicitly fictional reference summaries describe Atlas Retail, Cedar Industrial and Beacon Distribution. Reference interviews and final staff availability remain subject to confirmation.'}
]


def generate(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Brand',fontSize=11,textColor=colors.HexColor('#6546c9'),spaceAfter=16))
    def para(text,style='BodyText'):
        return Paragraph(text,styles[style])
    def header(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#666677'))
        canvas.drawString(42,25,'FICTIONAL CLASSROOM PROPOSAL - no real supplier or confidential information')
        canvas.drawRightString(A4[0]-42,25,f'Page {doc.page}')
    for item in PROFILES:
        story=[para('PROCUREMENT PORTAL | SYNTHETIC RFP','Brand'),para(item['name'],'Title'),para('Executive summary','Heading2'),para(item['summary']),Spacer(1,16),
               para('Understanding of the requirement','Heading2'),para('Build a supplier onboarding and procurement analytics portal with SSO, ERP integration, reporting, role-based access, audit logs, migration, training and post-launch support. This fictional proposal addresses the same procurement request as the other three fixtures.'),
               para('Proposed solution and architecture','Heading2'),para(item['solution']),PageBreak(),
               para('Delivery, team and milestones','Title'),para(item['plan']),Spacer(1,18),para('Commercial proposal (USD)','Heading2')]
        table=Table([['Cost item','Amount / assumption'],['Implementation',f'USD {item["price"]:,} fixed fee'],['Annual support',f'USD {item["annual"]:,} from year two'],['Three-year disclosed total',f'USD {item["price"]+2*item["annual"]:,}'],['Taxes','Excluded; customer statutory rate applies'],['Scope assumptions','One ERP, one SSO tenant, up to 10,000 suppliers'],['Exclusions','Travel, extra integrations and cloud consumption'] ],colWidths=[170,320])
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#ede8fb')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('LINEBELOW',(0,0),(-1,-1),0.3,colors.HexColor('#d6d3df'))]))
        story += [table,Spacer(1,18),para('Payment assumptions','Heading2'),para('Payment schedule: 20 percent at signed discovery, 40 percent at build acceptance and 40 percent at launch. Change requests require written scope and price agreement. Customer supplies ERP credentials, cleans source data and appoints acceptance reviewers.'),PageBreak(),
                  para('Security, support and experience','Title'),para('Security, privacy and risk controls','Heading2'),para(item['security']),Spacer(1,16),para('Support, experience and references','Heading2'),para(item['support']),Spacer(1,18),para('Risks and clarification points','Heading2'),para('All supplier claims require procurement due diligence. Any omitted commitment remains unconfirmed, not implicitly included. Pricing excludes taxes and variable cloud usage. The customer must validate integration access, data readiness and reference assertions before award.'),para('Fictional-data notice','Heading2'),para('Every company, project, reference and commercial amount in this proposal is invented for teaching. This is not an actual commercial offer or proof of certification.')]
        SimpleDocTemplate(str(output/item['file']),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=45,bottomMargin=42).build(story,onFirstPage=header,onLaterPages=header)

if __name__=='__main__':
    generate(Path(__file__).resolve().parents[1]/'fixtures/proposals')
