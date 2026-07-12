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
    @State private var activeBriefDate: IdentifiableString? = nil
    @State private var selectedBriefContent: String? = nil
    @State private var isFetchingBrief = false
    
    // Pulse details snapshot sheet
    @State private var activePulseSnapshot: APIPulseHistoryEntry? = nil
    @State private var snapshotDetails: [String: AnyDecodableValue]? = nil
    @State private var isFetchingSnapshot = false

    // Segmented control navigation for iOS view to avoid vertical layout bloating
    @State private var selectedSection: AlmanacSection = .dashboard

    enum AlmanacSection: String, CaseIterable, Identifiable {
        case dashboard = "Ingest"
        case briefs = "Briefs"
        case feed = "Live Feed & Matrix"
        
        var id: String { rawValue }
    }

    var body: some View {
        #if os(macOS)
        ScrollView {
            VStack(spacing: 20) {
                headerSection
                
                BudgetCardView(onHoldReleased: {
                    loadInitialDashboardData()
                })
                
                PulseActionGridView(
                    wikiEntities: wikiEntities,
                    activeTaskId: activeTaskId,
                    onDryRunTriggered: { triggerDailyAlmanacRun(dryRun: true) },
                    onLiveBriefTriggered: { triggerDailyAlmanacRun(dryRun: false) },
                    onPulseTriggered: { triggerPulse(for: $0) }
                )
                
                HStack(alignment: .top, spacing: 20) {
                    BriefsHistorySection(
                        history: almanacService.almanacHistory,
                        onBriefSelected: { openDailyBrief($0) }
                    )
                    PulsesHistorySection(
                        history: almanacService.pulseHistory,
                        onPulseSelected: { openPulseSnapshot($0) },
                        onPulseRerun: { triggerPulse(for: $0) }
                    )
                }
                .padding(.horizontal)
                
                EntanglementMatrixSection(
                    selectedEntityName: $selectedEntityName,
                    wikiEntities: wikiEntities,
                    isFetchingEntanglements: isFetchingEntanglements,
                    entanglements: entanglements,
                    divergence: divergence,
                    onEntitySelected: { fetchEntanglementData(for: $0) }
                )
                
                Color.clear.frame(height: 130)
            }
            .padding(.vertical)
        }
        .background(DesignConstants.warmBackground)
        .onAppear {
            loadInitialDashboardData()
        }
        .sheet(isPresented: $showConsoleSheet) { consoleSheetContent }
        .sheet(item: $activeBriefDate) { briefReaderSheetContent(ident: $0) }
        .sheet(item: $activePulseSnapshot) { pulseDetailsSheetContent(entry: $0) }
        #else
        VStack(spacing: 0) {
            Picker("Section", selection: $selectedSection) {
                ForEach(AlmanacSection.allCases) { sec in
                    Text(sec.rawValue).tag(sec)
                }
            }
            .pickerStyle(.segmented)
            .padding()
            .background(DesignConstants.cardBackground)
            
            ScrollView {
                VStack(spacing: 20) {
                    headerSection
                    
                    switch selectedSection {
                    case .dashboard:
                        BudgetCardView(onHoldReleased: {
                            loadInitialDashboardData()
                        })
                        
                        PulseActionGridView(
                            wikiEntities: wikiEntities,
                            activeTaskId: activeTaskId,
                            onDryRunTriggered: { triggerDailyAlmanacRun(dryRun: true) },
                            onLiveBriefTriggered: { triggerDailyAlmanacRun(dryRun: false) },
                            onPulseTriggered: { triggerPulse(for: $0) }
                        )
                        
                    case .briefs:
                        BriefsHistorySection(
                            history: almanacService.almanacHistory,
                            onBriefSelected: { openDailyBrief($0) }
                        )
                        
                    case .feed:
                        PulsesHistorySection(
                            history: almanacService.pulseHistory,
                            onPulseSelected: { openPulseSnapshot($0) },
                            onPulseRerun: { triggerPulse(for: $0) }
                        )
                        
                        EntanglementMatrixSection(
                            selectedEntityName: $selectedEntityName,
                            wikiEntities: wikiEntities,
                            isFetchingEntanglements: isFetchingEntanglements,
                            entanglements: entanglements,
                            divergence: divergence,
                            onEntitySelected: { fetchEntanglementData(for: $0) }
                        )
                    }
                }
                .padding(.vertical)
            }
            .background(DesignConstants.warmBackground)
        }
        .onAppear {
            loadInitialDashboardData()
        }
        .sheet(isPresented: $showConsoleSheet) { consoleSheetContent }
        .sheet(item: $activeBriefDate) { briefReaderSheetContent(ident: $0) }
        .sheet(item: $activePulseSnapshot) { pulseDetailsSheetContent(entry: $0) }
        #endif
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

    // MARK: - Sheets Content Helper Views

    @ViewBuilder
    private var consoleSheetContent: some View {
        if let taskId = activeTaskId, let taskName = activeTaskName {
            NavigationStack {
                TaskConsoleView(
                    taskId: taskId,
                    taskName: taskName,
                    onFinished: {
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

    @ViewBuilder
    private func briefReaderSheetContent(ident: IdentifiableString) -> some View {
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
                        activeBriefDate = nil
                        selectedBriefContent = nil
                    }
                }
            }
        }
        #if os(macOS)
        .frame(minWidth: 700, minHeight: 600)
        #endif
    }

    @ViewBuilder
    private func pulseDetailsSheetContent(entry: APIPulseHistoryEntry) -> some View {
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
            .navigationTitle("Ingest Snapshot: \(entry.entityName)")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") {
                        activePulseSnapshot = nil
                        snapshotDetails = nil
                    }
                }
            }
        }
        #if os(macOS)
        .frame(minWidth: 600, minHeight: 500)
        #endif
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
        activeBriefDate = IdentifiableString(value: date)
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
        activePulseSnapshot = entry
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
