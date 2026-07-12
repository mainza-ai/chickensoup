import SwiftUI
import SwiftData

@MainActor
struct SettingsView: View {
    var backendService = BackendService.shared
    
    @State private var selectedBackend: String = "numpy"
    @State private var ibmToken: String = ""
    @State private var dwaveToken: String = ""
    @State private var ionqToken: String = ""
    @State private var hardwareEnabled: Bool = false
    
    @State private var showIbmToken = false
    @State private var showDwaveToken = false
    @State private var showIonqToken = false
    
    @State private var isSaving = false
    @State private var saveSuccess = false
    @State private var saveMessage = ""
    
    @State private var llmSelectedModel: String = ""
    @State private var llmAvailableModels: [String] = []
    @State private var isSavingLLM = false
    @State private var llmSaveSuccess = false
    @State private var llmSaveMessage = ""
    @State private var selectedProvider: String = "auto"
    @State private var providerModels: [String: [String]] = [:]
    @State private var isProbingProvider = false
    
    // Living Almanac states
    @State private var selectedEntityForPulse: String = ""
    @State private var showingPulseResult: APIPulseResult? = nil
    @State private var showingPulseResultAlert = false
    @State private var showingAlmanacResult: APIAlmanacGenerateResponse? = nil
    @State private var showingAlmanacResultSheet = false
    
    // Background task log console states
    @State private var activeTaskId: String? = nil
    @State private var activeTaskName: String? = nil
    @State private var showConsoleSheet = false

    private var hasUnsavedChanges: Bool {
        selectedBackend != backendService.config.quantumBackend ||
        hardwareEnabled != backendService.config.quantumHardwareEnabled ||
        !ibmToken.isEmpty ||
        !dwaveToken.isEmpty ||
        !ionqToken.isEmpty ||
        selectedProvider != (backendService.config.llmActiveProvider.isEmpty ? "auto" : backendService.config.llmActiveProvider) ||
        (!llmSelectedModel.isEmpty && llmSelectedModel != backendService.config.llmActiveModel)
    }
    
    private let providerOptions = [
        ("auto", "Auto-detect"),
        ("omlx", "oMLX"),
        ("ollama", "Ollama"),
        ("lmstudio", "LM Studio"),
    ]
    
    let backends = [
        ("numpy", "NumPy Simulator (Classical)"),
        ("qiskit", "Qiskit Simulator (Quantum local)"),
        ("dwave", "D-Wave Ocean System"),
        ("ibm", "IBM Quantum QPU"),
        ("ionq", "IonQ Aria Trapped-Ion QPU")
    ]
    
    private var entities: [APIWikiPageListItem] {
        backendService.wiki.wikiPages.filter { $0.pageType == "entities" }
    }

    var body: some View {
        ScrollView {
            VStack(spacing: DesignConstants.loosePadding) {
                brandHeader
                headerBanner
                backendPickerSection
                llmConfigSection
                chatToWikiSection
                livingAlmanacSection
                apiTokenSection
            }
        }
        .background(DesignConstants.warmBackground)
        .navigationTitle("Configuration")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .onAppear {
            loadCurrentConfig()
            Task {
                await backendService.wiki.fetchWikiPages(pageType: "entities")
                await backendService.almanac.fetchBudgetStatus()
                await backendService.almanac.fetchPulseHistory()
                await backendService.almanac.fetchAlmanacHistory()
            }
        }
        .alert("Pulse Ingestion Completed", isPresented: $showingPulseResultAlert, presenting: showingPulseResult) { res in
            Button("OK", role: .cancel) { }
        } message: { res in
            if res.status == "success" {
                Text("Successfully ingested \(res.evidence.count) claims for \(res.entityName).\nRemaining budget: $\(String(format: "%.2f", res.budgetRemaining))")
            } else {
                Text("Ingestion failed: \(res.error ?? res.status)")
            }
        }
        .sheet(isPresented: $showingAlmanacResultSheet) {
            if let res = showingAlmanacResult {
                VStack(spacing: 20) {
                    Text(res.dryRun ? "Almanac Dry Run Summary" : "Almanac Generated")
                        .font(.title2)
                        .bold()
                        .padding(.top)

                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("Status:")
                                .bold()
                            Spacer()
                            Text(res.status)
                                .foregroundStyle(res.status == "success" ? .green : .red)
                        }
                        HStack {
                            Text("Date:")
                                .bold()
                            Spacer()
                            Text(res.date)
                        }
                        HStack {
                            Text("Entities Processed:")
                                .bold()
                            Spacer()
                            Text("\(res.entitiesProcessed)")
                        }
                        HStack {
                            Text("Claims Moved:")
                                .bold()
                            Spacer()
                            Text("\(res.claimsMoved)")
                        }
                        HStack {
                            Text("Claims Collapsed:")
                                .bold()
                            Spacer()
                            Text("\(res.claimsCollapsed)")
                        }
                        HStack {
                            Text("Newly Contested:")
                                .bold()
                            Spacer()
                            Text("\(res.newlyContested)")
                        }
                        HStack {
                            Text("Elapsed Time:")
                                .bold()
                            Spacer()
                            Text("\(String(format: "%.1f", res.elapsedSeconds))s")
                        }
                        if let err = res.error {
                            Text("Error: \(err)")
                                .foregroundStyle(.red)
                        }
                    }
                    .padding()
                    .background(Color.gray.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 10))

                    Spacer()

                    Button(action: {
                        showingAlmanacResultSheet = false
                    }) {
                        Text("Dismiss")
                            .bold()
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(DesignConstants.systemOrange)
                            .foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .padding(.horizontal)
                    .padding(.bottom)
                }
                .padding()
                .presentationDetents([.medium])
            }
        }
        .sheet(isPresented: $showConsoleSheet) {
            if let taskId = activeTaskId, let taskName = activeTaskName {
                NavigationStack {
                    TaskConsoleView(
                        taskId: taskId,
                        taskName: taskName,
                        onFinished: {
                            Task {
                                await backendService.almanac.fetchPulseHistory()
                                await backendService.almanac.fetchAlmanacHistory()
                                await backendService.almanac.fetchBudgetStatus()
                            }
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
        .safeAreaInset(edge: .bottom) {
            if hasUnsavedChanges {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Unsaved Changes")
                            .font(.caption)
                            .bold()
                            .foregroundStyle(DesignConstants.systemOrangeText)
                        Text("You have pending configuration updates.")
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    
                    Spacer()
                    
                    Button(action: saveAllSettings) {
                        HStack {
                            if isSaving {
                                ProgressView()
                                    .progressViewStyle(.circular)
                                    .scaleEffect(0.8)
                                    .padding(.trailing, 4)
                            } else {
                                Image(systemName: "arrow.up.doc.fill")
                            }
                            Text(isSaving ? "Saving..." : "Apply Changes")
                                .bold()
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(
                            LinearGradient(
                                colors: [DesignConstants.systemOrange, .purple],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.buttonCornerRadius))
                    }
                    .buttonStyle(.plain)
                    .disabled(isSaving)
                }
                .padding()
                .background(.ultraThinMaterial)
                .overlay(VStack { Divider(); Spacer() })
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
    }

    @ViewBuilder
    private var brandHeader: some View {
        VStack(spacing: 6) {
            Image("logo")
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(height: 48)

            Text("Project Chicken Soup")
                .font(.title2)
                .bold()
                .foregroundStyle(
                    LinearGradient(
                        colors: [DesignConstants.systemOrange, .purple],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )

            Text("Quantum Spacetime Navigator & Lore Engine")
                .font(.caption)
                .foregroundStyle(DesignConstants.secondaryText)
        }
        .padding(.top, DesignConstants.loosePadding)
    }

    @ViewBuilder
    private var headerBanner: some View {
        VStack(spacing: 8) {
            Text("Quantum & Engine Configuration")
                .font(.title2)
                .bold()
                .foregroundStyle(DesignConstants.primaryText)

            Text("Configure your simulation backends and link quantum cloud hardware APIs.")
                .font(.subheadline)
                .foregroundStyle(DesignConstants.secondaryText)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .padding(.top, DesignConstants.compactPadding)
    }

    @ViewBuilder
    private var backendPickerSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("SIMULATION & HARDWARE BACKEND")
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)

            VStack(spacing: 0) {
                ForEach(backends, id: \.0) { item in
                    Button(action: {
                        withAnimation(DesignConstants.hoverAnimation) {
                            selectedBackend = item.0
                        }
                    }) {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(item.1)
                                    .font(.body)
                                    .foregroundStyle(DesignConstants.primaryText)
                                Text(item.0 == "numpy" || item.0 == "qiskit" ? "Runs locally on CPU/simulation threads" : "Requires API Credentials for Cloud Jobs")
                                    .font(.caption2)
                                    .foregroundStyle(DesignConstants.secondaryText)
                            }
                            Spacer()
                            if selectedBackend == item.0 {
                                HStack(spacing: 6) {
                                    if selectedBackend != backendService.config.quantumBackend {
                                        Circle()
                                            .fill(DesignConstants.systemOrange)
                                            .frame(width: 6, height: 6)
                                    }
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundStyle(DesignConstants.systemOrange)
                                }
                            }
                        }
                        .padding(.vertical, 12)
                        .padding(.horizontal, 16)
                        .background(selectedBackend == item.0 ? DesignConstants.controlBackground : Color.clear)
                    }
                    .buttonStyle(.plain)

                    if item.0 != backends.last?.0 {
                        Divider()
                            .background(DesignConstants.dividerColor)
                    }
                }
            }
            .background(DesignConstants.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius)
                    .stroke(DesignConstants.glassBorderColor, lineWidth: 1)
            )
        }
        .padding(.horizontal)
    }

    @ViewBuilder
    private var llmConfigSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("LANGUAGE MODEL CONFIGURATION")
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)

            VStack(spacing: 16) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Current Provider")
                            .font(.body)
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                        if !backendService.config.llmActiveProvider.isEmpty {
                            HStack(spacing: 6) {
                                Circle()
                                    .fill(backendService.config.llmActiveProvider != "simulated" ? DesignConstants.systemGreen : DesignConstants.systemRed)
                                    .frame(width: 8, height: 8)
                                Text(backendService.config.llmActiveProvider)
                                    .font(.subheadline)
                                    .foregroundStyle(DesignConstants.systemOrangeText)
                            }
                        } else {
                            Text("Auto-discovering...")
                                .font(.subheadline)
                                .foregroundStyle(DesignConstants.secondaryText)
                        }
                    }
                    Spacer()
                }

                Divider().background(DesignConstants.dividerColor)

                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Select Provider")
                            .font(.body)
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                        
                        let sProvider = backendService.config.llmActiveProvider
                        let activeProv = sProvider.isEmpty ? "auto" : sProvider
                        if selectedProvider != activeProv {
                            Circle()
                                .fill(DesignConstants.systemOrange)
                                .frame(width: 6, height: 6)
                        }
                    }

                    Picker("Provider", selection: $selectedProvider) {
                        ForEach(providerOptions, id: \.0) { option in
                            HStack {
                                Text(option.1)
                                if option.0 == backendService.config.llmActiveProvider {
                                    Image(systemName: "checkmark")
                                        .foregroundStyle(DesignConstants.systemOrange)
                                }
                            }
                            .tag(option.0)
                        }
                    }
                    .pickerStyle(.menu)
                    .tint(DesignConstants.systemOrange)
                    .onChange(of: selectedProvider) { _, newValue in
                        if newValue != "auto" {
                            probeProvider(newValue)
                        } else {
                            refreshLLMModels()
                        }
                    }
                }

                Divider().background(DesignConstants.dividerColor)

                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Active Model")
                            .font(.body)
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                        
                        if !llmSelectedModel.isEmpty && llmSelectedModel != backendService.config.llmActiveModel {
                            Circle()
                                .fill(DesignConstants.systemOrange)
                                .frame(width: 6, height: 6)
                        }
                        
                        Spacer()
                        if isProbingProvider {
                            ProgressView()
                                .scaleEffect(0.7)
                        }
                    }

                    if llmAvailableModels.isEmpty {
                        Text("No models discovered. Select a provider above or check server status.")
                            .font(.caption)
                            .foregroundStyle(DesignConstants.secondaryText)
                    } else {
                        Picker("Model", selection: $llmSelectedModel) {
                            ForEach(llmAvailableModels, id: \.self) { model in
                                HStack {
                                    Text(model)
                                    if model == backendService.config.llmActiveModel {
                                        Image(systemName: "checkmark")
                                            .foregroundStyle(DesignConstants.systemOrange)
                                    }
                                }
                                .tag(model)
                            }
                        }
                        .pickerStyle(.menu)
                        .tint(DesignConstants.systemOrange)
                    }
                }


            }
            .padding(DesignConstants.standardPadding)
            .background(DesignConstants.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius)
                    .stroke(DesignConstants.glassBorderColor, lineWidth: 1)
            )
        }
        .padding(.horizontal)
    }

    @ViewBuilder
    private var chatToWikiSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("CHAT TO WIKI CONVERSION")
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)

            VStack(spacing: 16) {
                Toggle(isOn: Binding(
                    get: { backendService.chat.isChatWikiConversionEnabled },
                    set: { backendService.chat.isChatWikiConversionEnabled = $0 }
                )) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Auto-Convert Chat to Wiki")
                            .font(.body)
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                        Text("Periodically extracts entities, concepts, and projects from conversations and creates wiki pages.")
                            .font(.caption)
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                }
                .toggleStyle(SwitchToggleStyle(tint: DesignConstants.systemOrange))
                .padding(.vertical, 4)

                if backendService.chat.isChatWikiConversionEnabled {
                    Divider()
                        .background(DesignConstants.dividerColor)

                    Toggle(isOn: Binding(
                        get: { backendService.chat.chatWikiNotify },
                        set: { backendService.chat.chatWikiNotify = $0 }
                    )) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Notify When Pages Created")
                                .font(.body)
                                .bold()
                                .foregroundStyle(DesignConstants.primaryText)
                            Text("Shows a banner when new wiki pages are created from your conversations.")
                                .font(.caption)
                                .foregroundStyle(DesignConstants.secondaryText)
                        }
                    }
                    .toggleStyle(SwitchToggleStyle(tint: DesignConstants.systemOrange))

                    Divider()
                        .background(DesignConstants.dividerColor)

                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Minimum Conversation Length")
                                .font(.body)
                                .bold()
                                .foregroundStyle(DesignConstants.primaryText)
                            Spacer()
                            Text("\(backendService.chat.chatWikiMinConversationLength)")
                                .font(.system(.subheadline, design: .monospaced))
                                .foregroundStyle(DesignConstants.systemOrangeText)
                        }

                        Stepper("Messages", value: Binding(
                            get: { backendService.chat.chatWikiMinConversationLength },
                            set: { backendService.chat.chatWikiMinConversationLength = $0 }
                        ), in: 5...50, step: 5)
                        .labelsHidden()

                        Text("Conversations must have at least this many messages before extraction.")
                            .font(.caption)
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                }

                Divider()
                    .background(DesignConstants.dividerColor)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Your Wiki Name")
                        .font(.body)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)

                    HStack {
                        TextField("Primary Researcher", text: Binding(
                            get: { backendService.chat.userName },
                            set: { backendService.chat.userName = $0 }
                        ))
                        .font(.system(.body, design: .monospaced))
                        .textFieldStyle(.plain)
                        .padding(10)
                        .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))

                        Button("Rename") {
                            let name = backendService.chat.userName.trimmingCharacters(in: .whitespaces)
                            guard !name.isEmpty else { return }
                            Task {
                                await backendService.chat.setUserName(name)
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(DesignConstants.systemOrange)
                        .font(.caption)
                    }
                    Text("This name is used for your personal wiki entity page.")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
            }
            .padding(DesignConstants.standardPadding)
            .background(DesignConstants.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius)
                    .stroke(DesignConstants.glassBorderColor, lineWidth: 1)
            )
        }
        .padding(.horizontal)

        VStack(alignment: .leading, spacing: 12) {
            Text("WIKI BACKUP & RESTORE")
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)

            VStack(spacing: 16) {
                if backendService.wiki.isExportingWiki {
                    HStack {
                        ProgressView()
                            .scaleEffect(0.8)
                        Text("Exporting wiki...")
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.systemOrangeText)
                    }
                    .frame(maxWidth: .infinity)
                } else {
                    Button(action: {
                        Task {
                            let result = await backendService.wiki.exportWiki()
                            await MainActor.run {
                                if let r = result, r.success {
                                    print("Wiki exported: \(r.filepath) (\(r.pageCount) pages, \(r.sizeKb) KB)")
                                }
                            }
                        }
                    }) {
                        HStack {
                            Image(systemName: "square.and.arrow.down")
                            Text("Export Wiki")
                                .bold()
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(DesignConstants.systemOrange.opacity(0.15))
                        .foregroundStyle(DesignConstants.systemOrangeText)
                        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.buttonCornerRadius))
                        .overlay(
                            RoundedRectangle(cornerRadius: DesignConstants.buttonCornerRadius)
                                .stroke(DesignConstants.systemOrange.opacity(0.3), lineWidth: 1)
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(DesignConstants.standardPadding)
            .background(DesignConstants.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius)
                    .stroke(DesignConstants.glassBorderColor, lineWidth: 1)
            )
        }
        .padding(.horizontal)
    }

    @ViewBuilder
    private var livingAlmanacSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("LIVING ALMANAC & EVIDENCE")
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)

            VStack(spacing: 16) {
                // Subsection A: Status & Toggle info
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("last30days Ingestion Engine")
                            .font(.headline)
                            .foregroundStyle(DesignConstants.primaryText)
                        Text(backendService.config.last30daysEnabled ? "Active — ingesting live evidence feeds" : "Disabled — set LAST30DAYS_ENABLED=true in .env")
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    Spacer()
                    Circle()
                        .fill(backendService.config.last30daysEnabled ? Color.green : Color.gray)
                        .frame(width: 10, height: 10)
                }
                
                Divider()
                    .background(DesignConstants.dividerColor)

                // Subsection B: Budget
                if let budget = backendService.almanac.budgetStatus {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Monthly Budget Status")
                                .font(.subheadline)
                                .bold()
                                .foregroundStyle(DesignConstants.primaryText)
                            Spacer()
                            Text("\(budget.monthKey)")
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 2)
                                .background(Color.blue.opacity(0.15))
                                .clipShape(Capsule())
                        }

                        let spent = budget.spentUsd
                        let ceiling = budget.ceilingUsd
                        let ratio = ceiling > 0 ? spent / ceiling : 0.0
                        
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                Capsule()
                                    .fill(Color.gray.opacity(0.2))
                                    .frame(height: 8)
                                Capsule()
                                    .fill(ratio > 0.8 ? Color.red : DesignConstants.systemOrange)
                                    .frame(width: geo.size.width * CGFloat(min(ratio, 1.0)), height: 8)
                            }
                        }
                        .frame(height: 8)

                        HStack {
                            Text("Spent $\(String(format: "%.2f", spent)) of $\(String(format: "%.2f", ceiling))")
                                .font(.caption)
                                .foregroundStyle(DesignConstants.secondaryText)
                            Spacer()
                            Text("\(budget.pullsCount) pulls")
                                .font(.caption)
                                .foregroundStyle(DesignConstants.secondaryText)
                        }

                        if budget.onHold {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Image(systemName: "exclamationmark.triangle.fill")
                                        .foregroundStyle(.red)
                                    Text("Budget on HOLD (Remaining < 2× cost per pull)")
                                        .font(.caption)
                                        .bold()
                                        .foregroundStyle(.red)
                                }
                                
                                Button(action: {
                                    Task {
                                        _ = await backendService.almanac.approveBudgetHold()
                                    }
                                }) {
                                    Text("Approve Hold & Release Budget")
                                        .font(.caption)
                                        .bold()
                                        .padding(.vertical, 6)
                                        .padding(.horizontal, 12)
                                        .background(Color.red.opacity(0.15))
                                        .foregroundStyle(.red)
                                        .clipShape(Capsule())
                                        .overlay(Capsule().stroke(Color.red, lineWidth: 1))
                                }
                            }
                            .padding(8)
                            .background(Color.red.opacity(0.05))
                            .clipShape(RoundedRectangle(cornerRadius: 6))
                        }
                    }
                } else {
                    HStack {
                        Text("Budget status not fetched")
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.secondaryText)
                        Spacer()
                        Button(action: {
                            Task {
                                await backendService.almanac.fetchBudgetStatus()
                            }
                        }) {
                            Text("Fetch")
                                .font(.caption)
                                .bold()
                        }
                    }
                }

                Divider()
                    .background(DesignConstants.dividerColor)

                // Subsection C: Pulse Controls (Entity List)
                VStack(alignment: .leading, spacing: 8) {
                    Text("Entity Pulse Ingestion")
                        .font(.subheadline)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)
                    
                    if entities.isEmpty {
                        Text("No entities found to pulse. Check the wiki pages list.")
                            .font(.caption)
                            .foregroundStyle(DesignConstants.secondaryText)
                    } else {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                ForEach(entities.prefix(10)) { ent in
                                    Button(action: {
                                        selectedEntityForPulse = ent.slug
                                        activeTaskName = "Pulse: \(ent.title)"
                                        showConsoleSheet = true
                                        Task {
                                            if let res = await backendService.almanac.triggerPulseAsync(entityName: ent.slug) {
                                                await MainActor.run {
                                                    self.activeTaskId = res.taskId
                                                }
                                            } else {
                                                showConsoleSheet = false
                                            }
                                        }
                                    }) {
                                        HStack(spacing: 4) {
                                            Text(ent.title)
                                                .font(.caption)
                                                .foregroundStyle(DesignConstants.primaryText)
                                            Image(systemName: "bolt.fill")
                                                .font(.system(size: 10))
                                                .foregroundStyle(DesignConstants.systemOrange)
                                        }
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 6)
                                        .background(DesignConstants.controlBackground)
                                        .clipShape(Capsule())
                                        .overlay(Capsule().stroke(DesignConstants.dividerColor, lineWidth: 1))
                                    }
                                    .disabled(activeTaskId != nil || !backendService.config.last30daysEnabled)
                                }
                            }
                        }
                    }
                }

                Divider()
                    .background(DesignConstants.dividerColor)

                // Subsection D: Almanac Generation & History
                VStack(alignment: .leading, spacing: 10) {
                    Text("Almanac Generation")
                        .font(.subheadline)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)
                    
                    HStack(spacing: 12) {
                        Button(action: {
                            activeTaskName = "Almanac Dry Run"
                            showConsoleSheet = true
                            Task {
                                if let res = await backendService.almanac.generateAlmanacAsync(dryRun: true) {
                                    await MainActor.run {
                                        self.activeTaskId = res.taskId
                                    }
                                } else {
                                    showConsoleSheet = false
                                }
                            }
                        }) {
                            HStack {
                                Spacer()
                                Text("Dry Run Brief")
                                    .bold()
                                Spacer()
                            }
                            .padding(.vertical, 10)
                            .background(Color.blue.opacity(0.15))
                            .foregroundStyle(.blue)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                        .disabled(activeTaskId != nil)

                        Button(action: {
                            activeTaskName = "Generate Daily Almanac Brief"
                            showConsoleSheet = true
                            Task {
                                if let res = await backendService.almanac.generateAlmanacAsync(dryRun: false) {
                                    await MainActor.run {
                                        self.activeTaskId = res.taskId
                                    }
                                } else {
                                    showConsoleSheet = false
                                }
                            }
                        }) {
                            HStack {
                                Spacer()
                                Text("Generate Live")
                                    .bold()
                                Spacer()
                            }
                            .padding(.vertical, 10)
                            .background(backendService.config.last30daysEnabled ? DesignConstants.systemOrange : Color.gray)
                            .foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                        .disabled(activeTaskId != nil || !backendService.config.last30daysEnabled)
                    }

                    if !backendService.almanac.almanacHistory.isEmpty {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Recent Generated Briefs")
                                .font(.caption)
                                .bold()
                                .foregroundStyle(DesignConstants.secondaryText)
                            
                            ForEach(backendService.almanac.almanacHistory.prefix(3)) { brief in
                                HStack {
                                    Image(systemName: "doc.plaintext.fill")
                                        .foregroundStyle(DesignConstants.systemOrange)
                                    Text(brief.date)
                                        .font(.caption)
                                        .bold()
                                        .foregroundStyle(DesignConstants.primaryText)
                                    Spacer()
                                    Text("\(String(format: "%.1f", brief.sizeKb)) KB")
                                        .font(.caption)
                                        .foregroundStyle(DesignConstants.secondaryText)
                                }
                                .padding(.vertical, 4)
                            }
                        }
                        .padding(.top, 4)
                    }
                }
            }
            .padding(DesignConstants.standardPadding)
            .background(DesignConstants.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius)
                    .stroke(DesignConstants.glassBorderColor, lineWidth: 1)
            )
        }
        .padding(.horizontal)
    }

    @ViewBuilder
    private var apiTokenSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("QUANTUM HARDWARE CONNECTIVITY")
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)

            VStack(spacing: 16) {
                HStack {
                    Toggle(isOn: $hardwareEnabled) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Enable Quantum QPU Dispatch")
                                .font(.body)
                                .bold()
                                .foregroundStyle(DesignConstants.primaryText)
                            Text("Allows submitting real quantum circuits to IBM, D-Wave, or IonQ instead of fallback local simulation threads.")
                                .font(.caption)
                                .foregroundStyle(DesignConstants.secondaryText)
                        }
                    }
                    .toggleStyle(SwitchToggleStyle(tint: DesignConstants.systemOrange))
                    .padding(.vertical, 4)
                    
                    if hardwareEnabled != backendService.config.quantumHardwareEnabled {
                        Circle()
                            .fill(DesignConstants.systemOrange)
                            .frame(width: 6, height: 6)
                    }
                }

                Divider()
                    .background(DesignConstants.dividerColor)

                credentialField(
                    title: "IBM Quantum API Token",
                    placeholder: "Enter IBMQ Token...",
                    text: $ibmToken,
                    show: $showIbmToken,
                    isSetOnServer: backendService.config.ibmApiTokenSet,
                    isDirty: !ibmToken.isEmpty
                )

                Divider()
                    .background(DesignConstants.dividerColor)

                credentialField(
                    title: "D-Wave Ocean Token",
                    placeholder: "Enter D-Wave API Token...",
                    text: $dwaveToken,
                    show: $showDwaveToken,
                    isSetOnServer: backendService.config.dwaveApiTokenSet,
                    isDirty: !dwaveToken.isEmpty
                )

                Divider()
                    .background(DesignConstants.dividerColor)

                credentialField(
                    title: "IonQ API Token",
                    placeholder: "Enter IonQ API Token...",
                    text: $ionqToken,
                    show: $showIonqToken,
                    isSetOnServer: backendService.config.ionqApiTokenSet,
                    isDirty: !ionqToken.isEmpty
                )
            }
            .padding(DesignConstants.standardPadding)
            .background(DesignConstants.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius)
                    .stroke(DesignConstants.glassBorderColor, lineWidth: 1)
            )
        }
        .padding(.horizontal)
    }



    @ViewBuilder
    private func credentialField(
        title: String,
        placeholder: String,
        text: Binding<String>,
        show: Binding<Bool>,
        isSetOnServer: Bool,
        isDirty: Bool = false
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                HStack(spacing: 6) {
                    Text(title)
                        .font(.subheadline)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)
                    
                    if isDirty {
                        Circle()
                            .fill(DesignConstants.systemOrange)
                            .frame(width: 6, height: 6)
                    }
                }
                
                Spacer()
                
                if isSetOnServer {
                    HStack(spacing: 4) {
                        Image(systemName: "lock.shield.fill")
                            .font(.caption)
                        Text("Active on Server")
                            .font(.caption2)
                    }
                    .foregroundStyle(DesignConstants.systemGreenText)
                } else {
                    Text("Not Configured")
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
            }
            
            HStack {
                if show.wrappedValue {
                    TextField(placeholder, text: text)
                        .font(.system(.body, design: .monospaced))
                } else {
                    SecureField(isSetOnServer ? "••••••••••••••••" : placeholder, text: text)
                        .font(.system(.body, design: .monospaced))
                }
                
                Button(action: { show.wrappedValue.toggle() }) {
                    Image(systemName: show.wrappedValue ? "eye.slash" : "eye")
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.plain)
            }
            .padding(10)
            .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))
        }
    }
    
    private func loadCurrentConfig() {
        Task {
            await backendService.fetchConfig()
            self.selectedBackend = backendService.config.quantumBackend
            self.hardwareEnabled = backendService.config.quantumHardwareEnabled
            self.ibmToken = ""
            self.dwaveToken = ""
            self.ionqToken = ""
            self.selectedProvider = "auto"
            self.llmAvailableModels = backendService.config.llmAvailableModels
            self.llmSelectedModel = backendService.config.llmActiveModel
        }
    }
    
    private func refreshLLMModels() {
        Task {
            await backendService.config.refreshLLMDiscovery()
            self.llmAvailableModels = backendService.config.llmAvailableModels
            self.llmSelectedModel = backendService.config.llmActiveModel
        }
    }
    
    private func probeProvider(_ name: String) {
        isProbingProvider = true
        llmAvailableModels = []
        llmSelectedModel = ""
        
        Task {
            let result = await backendService.config.probeLLMProvider(name)
            await MainActor.run {
                isProbingProvider = false
                if result.available {
                    self.llmAvailableModels = result.models
                    self.llmSelectedModel = result.models.first ?? ""
                } else {
                    self.llmAvailableModels = []
                    self.llmSaveMessage = "Provider '\(name)' is not available."
                    self.llmSaveSuccess = false
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                        withAnimation { self.llmSaveMessage = "" }
                    }
                }
            }
        }
    }
    
    private func saveAllSettings() {
        isSaving = true
        saveMessage = ""
        
        Task {
            var success = true
            
            // 1. Save Quantum if modified
            let quantumModified = selectedBackend != backendService.config.quantumBackend ||
                                  hardwareEnabled != backendService.config.quantumHardwareEnabled ||
                                  !ibmToken.isEmpty ||
                                  !dwaveToken.isEmpty ||
                                  !ionqToken.isEmpty
            
            if quantumModified {
                let qSuccess = await backendService.config.saveConfig(
                    backend: selectedBackend,
                    ibmToken: ibmToken,
                    dwaveToken: dwaveToken,
                    ionqToken: ionqToken,
                    hardwareEnabled: hardwareEnabled
                )
                if !qSuccess { success = false }
            }
            
            // 2. Save LLM if modified
            let providerToUse = selectedProvider == "auto" ? nil : selectedProvider
            let llmModified = selectedProvider != (backendService.config.llmActiveProvider.isEmpty ? "auto" : backendService.config.llmActiveProvider) ||
                              (!llmSelectedModel.isEmpty && llmSelectedModel != backendService.config.llmActiveModel)
            
            if llmModified && !llmSelectedModel.isEmpty {
                let lSuccess = await backendService.config.saveLLMConfig(
                    provider: providerToUse,
                    model: llmSelectedModel
                )
                if !lSuccess { success = false }
            }
            
            await MainActor.run {
                isSaving = false
                saveSuccess = success
                if success {
                    saveMessage = "Configuration updated successfully."
                    // Clear typed tokens so they return to mask state
                    ibmToken = ""
                    dwaveToken = ""
                    ionqToken = ""
                    
                    // Reload to reflect server state
                    loadCurrentConfig()
                    
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                        withAnimation {
                            if saveMessage.contains("successfully") {
                                saveMessage = ""
                            }
                        }
                    }
                } else {
                    saveMessage = "Failed to update configuration on server."
                }
            }
        }
    }
}

// MARK: - Preview

struct SettingsView_PreviewHelper: View {
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

        let events = [
            TemporalEvent(
                title: "Magenta UFO Crash Recovery",
                eventDescription: "A circular flying craft crash-landed in northern Italy, recovered by Mussolini's secret cabinet.",
                timestamp: Calendar.current.date(from: DateComponents(year: 1933, month: 6, day: 13)) ?? Date(),
                confidence: 0.94,
                source: "Mussolini Archives",
                type: "crash"
            ),
            TemporalEvent(
                title: "S-4 Propulsion Research",
                eventDescription: "Bob Lazar worked on back-engineering gravity amplifiers utilizing Element 115.",
                timestamp: Calendar.current.date(from: DateComponents(year: 1989, month: 12, day: 1)) ?? Date(),
                confidence: 0.92,
                source: "Bob Lazar Testimony",
                type: "theory"
            )
        ]

        for event in events {
            event.branch = mainBranch
            context.insert(event)
        }

        context.insert(LoreEntity(name: "Bob Lazar", type: "Person", summary: "S-4 whistleblower.", confidence: 0.90, source: "S-4 Records"))

        self.container = container
    }

    var body: some View {
        SettingsView()
            .modelContainer(container)
            .environment(AlmanacService.shared)
            .environment(BackendService.shared)
    }
}

#Preview {
    SettingsView_PreviewHelper()
}
