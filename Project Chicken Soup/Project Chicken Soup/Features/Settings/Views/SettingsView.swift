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
                // Header Banner
                VStack(spacing: 8) {
                    Image(systemName: "slider.horizontal.3")
                        .font(.system(size: 40))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [DesignConstants.systemOrange, .purple],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .padding(.bottom, 8)
                    
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
                .padding(.top, DesignConstants.loosePadding)
                
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
                
                // Section 2: Hardware Toggles and Credentials
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
                            isSetOnServer: backendService.ibmApiTokenSet
                        )
                        
                        Divider()
                            .background(DesignConstants.dividerColor)
                        
                        // D-Wave token
                        credentialField(
                            title: "D-Wave Ocean Token",
                            placeholder: "Enter D-Wave API Token...",
                            text: $dwaveToken,
                            show: $showDwaveToken,
                            isSetOnServer: backendService.dwaveApiTokenSet
                        )
                        
                        Divider()
                            .background(DesignConstants.dividerColor)
                        
                        // IonQ token
                        credentialField(
                            title: "IonQ API Token",
                            placeholder: "Enter IonQ API Token...",
                            text: $ionqToken,
                            show: $showIonqToken,
                            isSetOnServer: backendService.ionqApiTokenSet
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
            self.selectedBackend = backendService.quantumBackend
            self.hardwareEnabled = backendService.quantumHardwareEnabled
            self.ibmToken = ""
            self.dwaveToken = ""
            self.ionqToken = ""
        }
    }
    
    private func saveSettings() {
        isSaving = true
        saveMessage = ""
        
        Task {
            let success = await backendService.saveConfig(
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
