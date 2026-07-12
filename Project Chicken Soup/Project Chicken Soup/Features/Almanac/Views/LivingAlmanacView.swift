import SwiftUI
import WebKit
import SwiftData

struct LivingAlmanacView: View {
    @Environment(AlmanacService.self) private var almanacService
    @Environment(\.modelContext) private var modelContext
    var backendService = BackendService.shared
    
    // Wiki pages list
    @State private var wikiEntities: [APIWikiPageListItem] = []
    
    // Interactive Entanglement explorer
    @State private var selectedEntityName: String = ""
    @State private var entanglements: [APIEntanglementEntry] = []
    @State private var divergence: APIDivergenceResult? = nil
    @State private var isFetchingEntanglements = false
    
    // Background execution task sheets
    @State private var activeTaskId: String? = nil
    @State private var activeTaskName: String? = nil
    @State private var showConsoleSheet = false
    
    // Brief reader sheet
    @State private var selectedBriefDate: String? = nil
    @State private var selectedBriefContent: String? = nil
    @State private var isFetchingBrief = false
    
    // Pulse details snapshot sheet
    @State private var selectedPulseSnapshot: APIPulseHistoryEntry? = nil
    @State private var snapshotDetails: [String: AnyDecodableValue]? = nil
    @State private var isFetchingSnapshot = false

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header with status indicator
                headerSection
                
                // Ingestion Budget Progress Card
                budgetCardSection
                
                // Action Grid: Quick Ingestion Pulse
                pulseActionSection
                
            // Live Activity & Feeds (side-by-side on macOS, stacked on iOS)
            Group {
                #if os(macOS)
                HStack(alignment: .top, spacing: 20) {
                    briefsHistorySection
                    pulsesHistorySection
                }
                #else
                VStack(spacing: 16) {
                    briefsHistorySection
                    pulsesHistorySection
                }
                #endif
            }
            .frame(maxWidth: .infinity)
            .padding(.horizontal)
                
                // Entanglement & Spacetime Metric Matrix Explorer
                entanglementMatrixSection
            }
            .padding(.vertical)
        }
        .background(DesignConstants.warmBackground)
        .onAppear {
            loadInitialDashboardData()
        }
        // Task Console Drawer/Sheet
        .sheet(isPresented: $showConsoleSheet) {
            if let taskId = activeTaskId, let taskName = activeTaskName {
                NavigationStack {
                    TaskConsoleView(
                        taskId: taskId,
                        taskName: taskName,
                        onFinished: {
                            // Refresh data on finish
                            loadInitialDashboardData()
                        },
                        onDismiss: {
                            showConsoleSheet = false
                            activeTaskId = nil
                            activeTaskName = nil
                        }
                    )
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Close") {
                                showConsoleSheet = false
                                activeTaskId = nil
                                activeTaskName = nil
                            }
                        }
                    }
                }
                #if os(macOS)
                .frame(minWidth: 500, minHeight: 400)
                #endif
            }
        }
        // Brief Reader Sheet
        .sheet(item: Binding<IdentifiableString?>(
            get: { selectedBriefDate.map { IdentifiableString(value: $0) } },
            set: { selectedBriefDate = $0?.value }
        )) { ident in
            NavigationStack {
                VStack {
                    if isFetchingBrief {
                        VStack(spacing: 12) {
                            ProgressView()
                            Text("Retrieving historical brief...")
                                .font(.caption)
                                .foregroundStyle(DesignConstants.secondaryText)
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else if let content = selectedBriefContent {
                        HTMLView(htmlContent: content)
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else {
                        ContentUnavailableView("Failed to load Brief", systemImage: "xmark.octagon", description: Text("Content is unavailable on server."))
                    }
                }
                .navigationTitle("Almanac Brief: \(ident.value)")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Close") {
                            selectedBriefDate = nil
                            selectedBriefContent = nil
                        }
                    }
                }
            }
            #if os(macOS)
            .frame(minWidth: 700, minHeight: 600)
            #endif
        }
        // Pulse Snapshot details sheet
        .sheet(item: Binding<IdentifiablePulse?>(
            get: { selectedPulseSnapshot.map { IdentifiablePulse(pulse: $0) } },
            set: { selectedPulseSnapshot = $0?.pulse }
        )) { ident in
            NavigationStack {
                VStack {
                    if isFetchingSnapshot {
                        VStack(spacing: 12) {
                            ProgressView()
                            Text("Loading pulse snapshot claims...")
                                .font(.caption)
                                .foregroundStyle(DesignConstants.secondaryText)
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else if let details = snapshotDetails {
                        PulseSnapshotDetailsView(details: details)
                    } else {
                        ContentUnavailableView("Pulse data missing", systemImage: "xmark.octagon")
                    }
                }
                .navigationTitle("Ingest Snapshot: \(ident.pulse.entityName)")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Close") {
                            selectedPulseSnapshot = nil
                            snapshotDetails = nil
                        }
                    }
                }
            }
            #if os(macOS)
            .frame(minWidth: 600, minHeight: 500)
            #endif
        }
    }
    
    // MARK: - Subsections
    
    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 6) {
                Text("LIVING ALMANAC")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(DesignConstants.systemOrangeText)
                
                Text("Spacetime Ingestion Workspace")
                    .font(.title)
                    .bold()
                    .foregroundStyle(DesignConstants.primaryText)
            }
            
            Spacer()
            
            // Last30days Status Indicator badge
            HStack(spacing: 6) {
                Circle()
                    .fill(almanacService.budgetStatus?.onHold == true ? DesignConstants.systemRed : (backendService.config.last30daysEnabled ? DesignConstants.systemGreen : .gray))
                    .frame(width: 8, height: 8)
                
                Text(almanacService.budgetStatus?.onHold == true ? "Budget Hold" : (backendService.config.last30daysEnabled ? "Active Ingestion" : "Disabled"))
                    .font(.caption)
                    .bold()
                    .foregroundStyle(DesignConstants.primaryText)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(DesignConstants.cardBackground)
            .clipShape(Capsule())
            .overlay(Capsule().stroke(DesignConstants.glassBorderColor, lineWidth: 1))
        }
        .padding(.horizontal)
    }
    
    private var budgetCardSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("API ENDPOINT BUDGET")
                        .font(.caption2)
                        .bold()
                        .foregroundStyle(DesignConstants.secondaryText)
                    
                    if let key = almanacService.budgetStatus?.monthKey {
                        Text("Current Cycle: \(key)")
                            .font(.subheadline)
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                    }
                }
                
                Spacer()
                
                if almanacService.isFetchingBudget {
                    ProgressView().progressViewStyle(.circular).scaleEffect(0.8)
                } else {
                    Button(action: {
                        Task { await almanacService.fetchBudgetStatus() }
                    }) {
                        Image(systemName: "arrow.clockwise")
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.systemOrange)
                    }
                    .buttonStyle(.plain)
                }
            }
            
            if let budget = almanacService.budgetStatus {
                let spent = budget.spentUsd
                let ceiling = budget.ceilingUsd
                let progress = ceiling > 0 ? spent / ceiling : 0.0
                
                VStack(alignment: .leading, spacing: 8) {
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            Rectangle()
                                .fill(Color.gray.opacity(0.15))
                            Rectangle()
                                .fill(budget.onHold ? DesignConstants.systemRed : (progress > 0.8 ? Color.red : DesignConstants.systemOrange))
                                .frame(width: geo.size.width * CGFloat(min(progress, 1.0)))
                        }
                    }
                    .frame(height: 10)
                    .clipShape(Capsule())
                    
                    HStack {
                        Text(String(format: "$%.2f Spent", spent))
                            .font(.system(.caption, design: .monospaced))
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                        
                        Spacer()
                        
                        Text(String(format: "$%.2f Ceiling", ceiling))
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    
                    HStack {
                        Label("\(budget.pullsCount) pulls performed", systemImage: "network")
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.secondaryText)
                        
                        Spacer()
                        
                        Text("Remaining: \(String(format: "$%.2f", budget.remainingUsd))")
                            .font(.system(.caption2, design: .monospaced))
                            .bold()
                            .foregroundStyle(budget.remainingUsd > 0 ? DesignConstants.systemGreenText : DesignConstants.systemRed)
                    }
                }
                
                if budget.onHold {
                    VStack(spacing: 12) {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundStyle(DesignConstants.systemRed)
                            Text("API SPENDING SAFETY HOLD ACTIVE")
                                .font(.caption)
                                .bold()
                                .foregroundStyle(DesignConstants.systemRed)
                        }
                        
                        Text("The monthly budget limit has been reached or triggered manual safety controls. Confirm approval to release hold.")
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.secondaryText)
                            .multilineTextAlignment(.center)
                        
                        Button("Approve and Release Hold") {
                            Task {
                                let success = await almanacService.approveBudgetHold()
                                if success {
                                    loadInitialDashboardData()
                                }
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(DesignConstants.systemRed)
                        .controlSize(.small)
                        .bold()
                    }
                    .padding()
                    .background(Color.red.opacity(0.08))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.systemRed.opacity(0.3), lineWidth: 1))
                }
            } else {
                Text("Ingestion budget status unavailable. Turn on active network settings in .env.")
                    .font(.caption2)
                    .foregroundStyle(DesignConstants.secondaryText)
            }
        }
        .padding()
        .background(DesignConstants.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
        .overlay(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius).stroke(DesignConstants.glassBorderColor, lineWidth: 1))
        .padding(.horizontal)
    }
    
    private var pulseActionSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("QUICK INGESTION INITIATOR")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(DesignConstants.systemOrangeText)
                
                Spacer()
                
                Button(action: {
                    triggerDailyAlmanacRun(dryRun: true)
                }) {
                    Label("Almanac Dry Run", systemImage: "doc.text.magnifyingglass")
                        .font(.caption2)
                        .bold()
                        .foregroundStyle(DesignConstants.systemOrange)
                }
                .buttonStyle(.plain)
                .disabled(activeTaskId != nil)
                
                Text("|")
                    .font(.caption2)
                    .foregroundStyle(DesignConstants.dividerColor)
                
                Button(action: {
                    triggerDailyAlmanacRun(dryRun: false)
                }) {
                    Label("Generate Live Brief", systemImage: "book.pages")
                        .font(.caption2)
                        .bold()
                        .foregroundStyle(.purple)
                }
                .buttonStyle(.plain)
                .disabled(activeTaskId != nil)
            }
            .padding(.horizontal)
            
            if wikiEntities.isEmpty {
                Text("No active wiki entities found in database. Ingest markdown source files first.")
                    .font(.caption2)
                    .foregroundStyle(DesignConstants.secondaryText)
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .center)
                    .background(DesignConstants.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(DesignConstants.glassBorderColor, lineWidth: 1))
                    .padding(.horizontal)
            } else {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        ForEach(wikiEntities) { ent in
                            Button(action: {
                                triggerPulse(for: ent.slug)
                            }) {
                                HStack(spacing: 8) {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(ent.title)
                                            .font(.subheadline)
                                            .bold()
                                            .foregroundStyle(DesignConstants.primaryText)
                                        Text("Slug: \(ent.slug)")
                                            .font(.caption2)
                                            .foregroundStyle(DesignConstants.secondaryText)
                                    }
                                    
                                    Image(systemName: "bolt.fill")
                                        .font(.caption)
                                        .foregroundStyle(DesignConstants.systemOrange)
                                }
                                .padding(.horizontal, 14)
                                .padding(.vertical, 10)
                                .background(DesignConstants.controlBackground)
                                .clipShape(RoundedRectangle(cornerRadius: 10))
                                .overlay(RoundedRectangle(cornerRadius: 10).stroke(DesignConstants.glassBorderColor, lineWidth: 1))
                            }
                            .buttonStyle(.plain)
                            .disabled(activeTaskId != nil)
                        }
                    }
                    .padding(.horizontal)
                }
            }
        }
    }
    
    private var briefsHistorySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("DAILY ALMANAC BRIEFS")
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)
            
            VStack(spacing: 10) {
                if almanacService.almanacHistory.isEmpty {
                    Text("No daily briefs compiled yet.")
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.secondaryText)
                        .padding(.vertical, 20)
                } else {
                    ForEach(almanacService.almanacHistory, id: \.filename) { brief in
                        Button(action: {
                            openDailyBrief(brief.date)
                        }) {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(brief.date)
                                        .font(.subheadline)
                                        .bold()
                                        .foregroundStyle(DesignConstants.primaryText)
                                    
                                    Text("\(brief.sizeKb) KB • Compiled on server")
                                        .font(.caption2)
                                        .foregroundStyle(DesignConstants.secondaryText)
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            .padding(10)
                            .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
                            .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding()
            .background(DesignConstants.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            .overlay(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius).stroke(DesignConstants.glassBorderColor, lineWidth: 1))
        }
    }
    
    private var pulsesHistorySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("SNAPSHOT FEED")
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)
            
            VStack(spacing: 10) {
                if almanacService.pulseHistory.isEmpty {
                    Text("No snapshots logged.")
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.secondaryText)
                        .padding(.vertical, 20)
                } else {
                    ForEach(almanacService.pulseHistory, id: \.file) { entry in
                        Button(action: {
                            openPulseSnapshot(entry)
                        }) {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(entry.entityName)
                                        .font(.subheadline)
                                        .bold()
                                        .foregroundStyle(DesignConstants.primaryText)
                                    Text("Pulsed: \(entry.date)")
                                        .font(.caption2)
                                        .foregroundStyle(DesignConstants.secondaryText)
                                }
                                
                                Spacer()
                                
                                Text("\(entry.evidenceCount) claims")
                                    .font(.system(.caption2, design: .monospaced))
                                    .bold()
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(DesignConstants.systemOrange.opacity(0.15))
                                    .foregroundStyle(DesignConstants.systemOrangeText)
                                    .clipShape(Capsule())
                            }
                            .padding(10)
                            .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
                            .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding()
            .background(DesignConstants.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            .overlay(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius).stroke(DesignConstants.glassBorderColor, lineWidth: 1))
        }
    }
    
    private var entanglementMatrixSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("SPACETIME ENTANGLEMENT MATRIX")
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)
                .padding(.horizontal)
            
            VStack(alignment: .leading, spacing: 16) {
                // Selector
                HStack(spacing: 12) {
                    Text("Explore Connections:")
                        .font(.subheadline)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)
                    
                    Picker("Select Entity", selection: $selectedEntityName) {
                        Text("Choose an entity...").tag("")
                        ForEach(wikiEntities) { ent in
                            Text(ent.title).tag(ent.title)
                        }
                    }
                    .pickerStyle(.menu)
                    .onChange(of: selectedEntityName) { _, newValue in
                        if !newValue.isEmpty {
                            fetchEntanglementData(for: newValue)
                        } else {
                            entanglements = []
                            divergence = nil
                        }
                    }
                    
                    Spacer()
                }
                
                if isFetchingEntanglements {
                    HStack {
                        Spacer()
                        VStack(spacing: 8) {
                            ProgressView()
                            Text("Solving spacetime entanglement equations...")
                                .font(.caption2)
                                .foregroundStyle(DesignConstants.secondaryText)
                        }
                        Spacer()
                    }
                    .padding(.vertical, 20)
                } else if !selectedEntityName.isEmpty {
                    // Divergence card
                    if let div = divergence {
                        #if os(macOS)
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("NARRATIVE DIVERGENCE RISK")
                                    .font(.caption2)
                                    .bold()
                                    .foregroundStyle(DesignConstants.secondaryText)
                                
                                HStack(spacing: 8) {
                                    Text(String(format: "%.1f%%", div.divergenceRisk * 100))
                                        .font(.system(.title3, design: .monospaced))
                                        .bold()
                                        .foregroundStyle(div.divergenceRisk > 0.5 ? DesignConstants.systemRed : DesignConstants.systemGreenText)
                                    
                                    Text(div.divergenceRisk > 0.5 ? "High Risk (Divergent)" : "Low Risk (Stable)")
                                        .font(.caption)
                                        .bold()
                                        .foregroundStyle(div.divergenceRisk > 0.5 ? DesignConstants.systemRed : DesignConstants.systemGreenText)
                                }
                            }
                            
                            Spacer()
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text("CANON HASH")
                                    .font(.caption2)
                                    .foregroundStyle(DesignConstants.secondaryText)
                                Text(div.canonVectorHash.prefix(8))
                                    .font(.system(.caption2, design: .monospaced))
                            }
                            
                            Spacer()
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text("LIVE SNAPSHOT HASH")
                                    .font(.caption2)
                                    .foregroundStyle(DesignConstants.secondaryText)
                                Text(div.liveVectorHash.prefix(8))
                                    .font(.system(.caption2, design: .monospaced))
                            }
                        }
                        .padding()
                        .background(DesignConstants.controlBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                        #else
                        VStack(alignment: .leading, spacing: 12) {
                            HStack(spacing: 8) {
                                Text(String(format: "%.1f%%", div.divergenceRisk * 100))
                                    .font(.system(.title3, design: .monospaced))
                                    .bold()
                                    .foregroundStyle(div.divergenceRisk > 0.5 ? DesignConstants.systemRed : DesignConstants.systemGreenText)
                                Text(div.divergenceRisk > 0.5 ? "High Risk (Divergent)" : "Low Risk (Stable)")
                                    .font(.caption)
                                    .bold()
                                    .foregroundStyle(div.divergenceRisk > 0.5 ? DesignConstants.systemRed : DesignConstants.systemGreenText)
                            }
                            HStack(spacing: 12) {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("CANON HASH")
                                        .font(.caption2)
                                        .foregroundStyle(DesignConstants.secondaryText)
                                    Text(div.canonVectorHash.prefix(8))
                                        .font(.system(.caption2, design: .monospaced))
                                }
                                Spacer()
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("LIVE SNAPSHOT HASH")
                                        .font(.caption2)
                                        .foregroundStyle(DesignConstants.secondaryText)
                                    Text(div.liveVectorHash.prefix(8))
                                        .font(.system(.caption2, design: .monospaced))
                                }
                            }
                        }
                        .padding()
                        .background(DesignConstants.controlBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                        #endif
                        
                        if !div.drivingClaims.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                Text("Divergence Drivers (Top claim anomalies):")
                                    .font(.caption)
                                    .bold()
                                    .foregroundStyle(DesignConstants.primaryText)
                                
                                ForEach(div.drivingClaims, id: \.claimText) { claim in
                                    HStack {
                                        Text(claim.claimText)
                                            .font(.caption2)
                                            .foregroundStyle(DesignConstants.primaryText)
                                        
                                        Spacer()
                                        
                                        let oldC = (claim.oldConfidence ?? 0.0) * 100.0
                                        let newC = claim.newConfidence * 100.0
                                        let deltaC = claim.delta * 100.0
                                        Text(String(format: "%.0f%% ➔ %.0f%% (Δ%.0f%%)", oldC, newC, deltaC))
                                            .font(.system(.caption2, design: .monospaced))
                                            .bold()
                                            .foregroundStyle(claim.delta > 0 ? DesignConstants.systemOrangeText : .purple)
                                    }
                                }
                            }
                        }
                    }
                    
                    Divider()
                        .background(DesignConstants.dividerColor)
                    
                    // Connection Matrix
                    if entanglements.isEmpty {
                        Text("No spacetime entanglements above baseline threshold computed.")
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.secondaryText)
                            .frame(maxWidth: .infinity, alignment: .center)
                    } else {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Entangled Spacetime Partners:")
                                .font(.caption)
                                .bold()
                                .foregroundStyle(DesignConstants.primaryText)
                            
                            ForEach(entanglements, id: \.entityB) { ent in
                                HStack {
                                    Image(systemName: "shared.with.you")
                                        .font(.caption)
                                        .foregroundStyle(DesignConstants.systemOrange)
                                    
                                    Text(ent.entityB)
                                        .font(.subheadline)
                                        .bold()
                                        .foregroundStyle(DesignConstants.primaryText)
                                    
                                    Spacer()
                                    
                                    HStack(spacing: 8) {
                                        Text("Co-occurrences: \(ent.coOccurrenceCount)")
                                            .font(.caption2)
                                            .foregroundStyle(DesignConstants.secondaryText)
                                        
                                        Text("Platforms: \(ent.independentPlatforms.joined(separator: ", "))")
                                            .font(.caption2)
                                            .foregroundStyle(DesignConstants.secondaryText)
                                        
                                        Text(String(format: "Entanglement: %.2f", ent.entanglementScore))
                                            .font(.system(.caption, design: .monospaced))
                                            .bold()
                                            .padding(.horizontal, 6)
                                            .padding(.vertical, 2)
                                            .background(DesignConstants.systemOrange.opacity(0.15))
                                            .foregroundStyle(DesignConstants.systemOrangeText)
                                            .clipShape(Capsule())
                                    }
                                }
                                .padding(10)
                                .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
                            }
                        }
                    }
                } else {
                    Text("Select a spacetime entity from the picker above to compute its correlation matrices.")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding(.vertical, 10)
                }
            }
            .padding()
            .background(DesignConstants.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            .overlay(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius).stroke(DesignConstants.glassBorderColor, lineWidth: 1))
            .padding(.horizontal)
        }
    }
    
    // MARK: - Actions
    
    private func loadInitialDashboardData() {
        Task {
            await backendService.config.fetchConfig()
            await almanacService.fetchBudgetStatus()
            await almanacService.fetchPulseHistory()
            await almanacService.fetchAlmanacHistory()
            await backendService.wiki.fetchWikiPages(pageType: "entities")
            await MainActor.run {
                self.wikiEntities = backendService.wiki.wikiPages.filter { $0.pageType == "entities" }
            }
        }
    }
    
    private func triggerPulse(for slug: String) {
        activeTaskName = "Pulse: \(slug.replacingOccurrences(of: "-", with: " ").capitalized)"
        showConsoleSheet = true
        Task {
            if let res = await almanacService.triggerPulseAsync(entityName: slug) {
                await MainActor.run {
                    self.activeTaskId = res.taskId
                }
            } else {
                showConsoleSheet = false
            }
        }
    }
    
    private func triggerDailyAlmanacRun(dryRun: Bool) {
        activeTaskName = "Almanac Generation \(dryRun ? "(Dry Run)" : "(Live)")"
        showConsoleSheet = true
        Task {
            if let res = await almanacService.generateAlmanacAsync(dryRun: dryRun) {
                await MainActor.run {
                    self.activeTaskId = res.taskId
                }
            } else {
                showConsoleSheet = false
            }
        }
    }
    
    private func openDailyBrief(_ date: String) {
        selectedBriefDate = date
        isFetchingBrief = true
        Task {
            if let content = await almanacService.fetchAlmanacFile(date: date) {
                await MainActor.run {
                    self.selectedBriefContent = content
                    self.isFetchingBrief = false
                }
            } else {
                await MainActor.run {
                    self.isFetchingBrief = false
                }
            }
        }
    }
    
    private func openPulseSnapshot(_ entry: APIPulseHistoryEntry) {
        selectedPulseSnapshot = entry
        isFetchingSnapshot = true
        Task {
            if let res = await almanacService.fetchPulseSnapshot(filePath: entry.file) {
                await MainActor.run {
                    self.snapshotDetails = res
                    self.isFetchingSnapshot = false
                }
            } else {
                await MainActor.run {
                    self.isFetchingSnapshot = false
                }
            }
        }
    }
    
    private func fetchEntanglementData(for name: String) {
        isFetchingEntanglements = true
        Task {
            let entRes = await almanacService.fetchEntanglement(entityName: name)
            let divRes = await almanacService.fetchDivergence(entityName: name)
            await MainActor.run {
                self.entanglements = entRes?.entanglements ?? []
                self.divergence = divRes
                self.isFetchingEntanglements = false
            }
        }
    }
}

// MARK: - Identifiable Helpers

struct IdentifiableString: Identifiable {
    let id = UUID()
    let value: String
}

struct IdentifiablePulse: Identifiable {
    let id = UUID()
    let pulse: APIPulseHistoryEntry
}

// MARK: - Preview

struct LivingAlmanacView_PreviewHelper: View {
    let container: ModelContainer

    init() {
        let schema = Schema([
            TemporalEvent.self,
            TimelineBranch.self,
            LoreEntity.self
        ])
        let container = try! ModelContainer(for: schema, configurations: [ModelConfiguration(isStoredInMemoryOnly: true)])
        let context = container.mainContext

        let mainBranch = TimelineBranch(name: "Universe Prime", isActive: true)
        context.insert(mainBranch)

        let event = TemporalEvent(
            title: "S-4 Propulsion Research",
            eventDescription: "Bob Lazar worked on back-engineering gravity amplifiers.",
            timestamp: Calendar.current.date(from: DateComponents(year: 1989, month: 12, day: 1)) ?? Date(),
            confidence: 0.92,
            source: "Bob Lazar Testimony",
            type: "theory"
        )
        event.branch = mainBranch
        context.insert(event)

        let entity = LoreEntity(name: "Bob Lazar", type: "Person", summary: "S-4 whistleblower.", confidence: 0.90, source: "S-4 Records")
        context.insert(entity)

        self.container = container
    }

    var body: some View {
        LivingAlmanacView()
            .modelContainer(container)
            .environment(AlmanacService.shared)
            .environment(BackendService.shared)
    }
}

#Preview {
    LivingAlmanacView_PreviewHelper()
}

// MARK: - HTMLView Representable

#if os(macOS)
struct HTMLView: NSViewRepresentable {
    let htmlContent: String
    func makeNSView(context: Context) -> WKWebView { WKWebView() }
    func updateNSView(_ nsView: WKWebView, context: Context) { nsView.loadHTMLString(htmlContent, baseURL: nil) }
}
#else
struct HTMLView: UIViewRepresentable {
    let htmlContent: String
    func makeUIView(context: Context) -> WKWebView { WKWebView() }
    func updateUIView(_ uiView: WKWebView, context: Context) { uiView.loadHTMLString(htmlContent, baseURL: nil) }
}
#endif

// MARK: - Pulse Snapshot Viewer

struct PulseSnapshotDetailsView: View {
    let details: [String: AnyDecodableValue]
    
    private var claims: [[String: AnyDecodableValue]] {
        if let arr = details["evidence"]?.asArray {
            return arr.compactMap { $0.asDictionary }
        }
        return []
    }
    
    var body: some View {
        List {
            Section("SNAPSHOT SUMMARY") {
                LabeledContent("Entity Name", value: details["entity_name"]?.asString ?? "")
                LabeledContent("Status", value: details["status"]?.asString ?? "")
                LabeledContent("Budget Remaining", value: String(format: "$%.2f", details["budget_remaining"]?.asDouble ?? 0.0))
            }
            
            Section("EVIDENCE CLAIMS COLLECTED (\(claims.count))") {
                if claims.isEmpty {
                    Text("No claims collected in this pulse snapshot.")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                } else {
                    ForEach(0..<claims.count, id: \.self) { idx in
                        let claim = claims[idx]
                        VStack(alignment: .leading, spacing: 6) {
                            Text(claim["claim_text"]?.asString ?? "Unknown Claim")
                                .font(.subheadline)
                                .bold()
                                .foregroundStyle(DesignConstants.primaryText)
                            
                            HStack {
                                if let platform = claim["source_platform"]?.asString {
                                    Text(platform.uppercased())
                                        .font(.caption2)
                                        .bold()
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(DesignConstants.controlBackground)
                                        .foregroundStyle(DesignConstants.secondaryText)
                                        .clipShape(Capsule())
                                }
                                
                                if let count = claim["engagement_count"]?.asInt {
                                    Text("Engagement: \(count)")
                                        .font(.caption2)
                                        .foregroundStyle(DesignConstants.secondaryText)
                                }
                                
                                Spacer()
                                
                                if let url = claim["url"]?.asString, let u = URL(string: url) {
                                    Link(destination: u) {
                                        Label("Source Link", systemImage: "link")
                                            .font(.caption2)
                                    }
                                }
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
        }
    }
}
