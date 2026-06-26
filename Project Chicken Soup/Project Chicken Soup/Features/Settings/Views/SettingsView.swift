import SwiftUI

struct SettingsView: View {
    @ObservedObject var backendService = BackendService.shared
    
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
    
    var body: some View {
        ScrollView {
            VStack(spacing: DesignConstants.loosePadding) {
                // Brand Header
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
                
                // Header Banner
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
                
                // Section 1: Dynamic Backend Picker
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
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundStyle(DesignConstants.systemOrange)
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
                
                // Section 2: LLM Configuration
                VStack(alignment: .leading, spacing: 12) {
                    Text("LANGUAGE MODEL CONFIGURATION")
                        .font(.caption)
                        .bold()
                        .foregroundStyle(DesignConstants.systemOrangeText)
                    
                    VStack(spacing: 16) {
                        // Active provider label (read-only)
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
                        
                        Divider()
                            .background(DesignConstants.dividerColor)
                        
                        // Provider picker
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Select Provider")
                                .font(.body)
                                .bold()
                                .foregroundStyle(DesignConstants.primaryText)
                            
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
                        
                        Divider()
                            .background(DesignConstants.dividerColor)
                        
                        // Model picker
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Active Model")
                                    .font(.body)
                                    .bold()
                                    .foregroundStyle(DesignConstants.primaryText)
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
                        
                        Divider()
                            .background(DesignConstants.dividerColor)
                        
                        // Save LLM config button
                        if !llmSaveMessage.isEmpty {
                            HStack {
                                Image(systemName: llmSaveSuccess ? "checkmark.seal.fill" : "exclamationmark.octagon.fill")
                                    .foregroundStyle(llmSaveSuccess ? DesignConstants.systemGreenText : DesignConstants.systemRed)
                                Text(llmSaveMessage)
                                    .font(.caption)
                                    .foregroundStyle(DesignConstants.primaryText)
                            }
                            .padding(8)
                            .background(llmSaveSuccess ? Color.green.opacity(0.1) : Color.red.opacity(0.1), in: Capsule())
                            .transition(.scale.combined(with: .opacity))
                        }
                        
                        Button(action: saveLLMSettings) {
                            HStack {
                                if isSavingLLM {
                                    ProgressView()
                                        .progressViewStyle(.circular)
                                        .scaleEffect(0.8)
                                        .padding(.trailing, 4)
                                } else {
                                    Image(systemName: "brain")
                                }
                                Text(isSavingLLM ? "Saving..." : "Apply Model Selection")
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
                        .disabled(isSavingLLM || llmAvailableModels.isEmpty)
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
                
                // Section 3: Chat-to-Wiki Conversion Settings
                VStack(alignment: .leading, spacing: 12) {
                    Text("CHAT TO WIKI CONVERSION")
                        .font(.caption)
                        .bold()
                        .foregroundStyle(DesignConstants.systemOrangeText)

                    VStack(spacing: 16) {
                        Toggle(isOn: Binding(
                            get: { backendService.isChatWikiConversionEnabled },
                            set: { backendService.isChatWikiConversionEnabled = $0 }
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

                        if backendService.isChatWikiConversionEnabled {
                            Divider()
                                .background(DesignConstants.dividerColor)

                            Toggle(isOn: Binding(
                                get: { backendService.chatWikiNotify },
                                set: { backendService.chatWikiNotify = $0 }
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
                                    Text("\(backendService.chatWikiMinConversationLength)")
                                        .font(.system(.subheadline, design: .monospaced))
                                        .foregroundStyle(DesignConstants.systemOrangeText)
                                }

                                Stepper("Messages", value: Binding(
                                    get: { backendService.chatWikiMinConversationLength },
                                    set: { backendService.chatWikiMinConversationLength = $0 }
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

                // Wiki Backup & Restore
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

                // Hardware Toggles and Credentials
                VStack(alignment: .leading, spacing: 12) {
                    Text("QUANTUM HARDWARE CONNECTIVITY")
                        .font(.caption)
                        .bold()
                        .foregroundStyle(DesignConstants.systemOrangeText)
                    
                    VStack(spacing: 16) {
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
                        
                        Divider()
                            .background(DesignConstants.dividerColor)
                        
                        // IBM token
                        credentialField(
                            title: "IBM Quantum API Token",
                            placeholder: "Enter IBMQ Token...",
                            text: $ibmToken,
                            show: $showIbmToken,
                            isSetOnServer: backendService.config.ibmApiTokenSet
                        )
                        
                        Divider()
                            .background(DesignConstants.dividerColor)
                        
                        // D-Wave token
                        credentialField(
                            title: "D-Wave Ocean Token",
                            placeholder: "Enter D-Wave API Token...",
                            text: $dwaveToken,
                            show: $showDwaveToken,
                            isSetOnServer: backendService.config.dwaveApiTokenSet
                        )
                        
                        Divider()
                            .background(DesignConstants.dividerColor)
                        
                        // IonQ token
                        credentialField(
                            title: "IonQ API Token",
                            placeholder: "Enter IonQ API Token...",
                            text: $ionqToken,
                            show: $showIonqToken,
                            isSetOnServer: backendService.config.ionqApiTokenSet
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
                
                // Save Button and Feedback UI
                VStack(spacing: 12) {
                    if !saveMessage.isEmpty {
                        HStack {
                            Image(systemName: saveSuccess ? "checkmark.seal.fill" : "exclamationmark.octagon.fill")
                                .foregroundStyle(saveSuccess ? DesignConstants.systemGreenText : DesignConstants.systemRed)
                            Text(saveMessage)
                                .font(.caption)
                                .foregroundStyle(DesignConstants.primaryText)
                        }
                        .padding(8)
                        .background(saveSuccess ? Color.green.opacity(0.1) : Color.red.opacity(0.1), in: Capsule())
                        .transition(.scale.combined(with: .opacity))
                    }
                    
                    Button(action: saveSettings) {
                        HStack {
                            if isSaving {
                                ProgressView()
                                    .progressViewStyle(.circular)
                                    .scaleEffect(0.8)
                                    .padding(.trailing, 4)
                            } else {
                                Image(systemName: "arrow.up.doc.fill")
                            }
                            Text(isSaving ? "Persisting..." : "Save Configuration")
                                .bold()
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
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
                .padding(.horizontal)
                .padding(.bottom, DesignConstants.loosePadding)
            }
        }
        .background(DesignConstants.warmBackground)
        .navigationTitle("Configuration")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .onAppear {
            loadCurrentConfig()
        }
    }
    
    @ViewBuilder
    private func credentialField(
        title: String,
        placeholder: String,
        text: Binding<String>,
        show: Binding<Bool>,
        isSetOnServer: Bool
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(title)
                    .font(.subheadline)
                    .bold()
                    .foregroundStyle(DesignConstants.primaryText)
                
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
    
    private func saveLLMSettings() {
        guard !llmSelectedModel.isEmpty else { return }
        isSavingLLM = true
        llmSaveMessage = ""
        
        Task {
            let providerToUse = selectedProvider == "auto" ? nil : selectedProvider
            let success = await backendService.config.saveLLMConfig(
                provider: providerToUse,
                model: llmSelectedModel
            )
            
            await MainActor.run {
                isSavingLLM = false
                llmSaveSuccess = success
                if success {
                    llmSaveMessage = "Model selection updated successfully."
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                        withAnimation {
                            if llmSaveMessage.contains("success") {
                                llmSaveMessage = ""
                            }
                        }
                    }
                } else {
                    llmSaveMessage = "Failed to update model selection on server."
                }
            }
        }
    }
    
    private func saveSettings() {
        isSaving = true
        saveMessage = ""
        
        Task {
            let success = await backendService.config.saveConfig(
                backend: selectedBackend,
                ibmToken: ibmToken,
                dwaveToken: dwaveToken,
                ionqToken: ionqToken,
                hardwareEnabled: hardwareEnabled
            )
            
            await MainActor.run {
                isSaving = false
                saveSuccess = success
                if success {
                    saveMessage = "Quantum engine config updated successfully."
                    // Clear inputs on success so they return to password mask
                    ibmToken = ""
                    dwaveToken = ""
                    ionqToken = ""
                    
                    // Dismiss message after delay
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                        withAnimation {
                            if saveMessage.contains("success") {
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
