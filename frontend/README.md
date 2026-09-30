# 🛡️ SentinEx Guard - Reviewer Console Frontend

The frontend reviewer console for SentinEx Guard is built with **React 19**, **Vite**, **Vanilla CSS** design system tokens, and **Lucide React** icons.

## Features
- **Real-Time KPI Dashboard**: Metrics cards tracking total volume, flagged transactions, pending reviews, confirmed fraud, and rules trigger distribution.
- **Transaction Table**: Filterable review queue (`FLAGGED`, `UNDER_REVIEW`, `CLEARED`, `CONFIRMED_FRAUD`) with search and quick-clear actions.
- **Deep-Dive Investigation Modal**: Granular rule breakdown, risk severity badges, full geolocation/device telemetry, and reviewer audit submission notes.
- **Interactive Rules Manager**: Real-time rule toggling, parameter tuning, and weight inspection.
- **Transaction Simulator**: Test simulated transaction payloads with instantaneous risk score evaluations.
- **Notification Inbox**: Audit log viewer for dispatched AWS SES and SNS fraud alerts.

## Development
```bash
npm install
npm run dev
```

## Production Build
```bash
npm run build
```
The production bundle is served via Nginx in Docker Compose.
