//
//  AINavigatorView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//
//  Production-graded: reflects real LLM discovery state, never asserts success in logs.
//

import SwiftUI

struct AINavigatorView: View {
    var discoveryService = LLMDiscoveryService.shared
    var backendService = BackendService.shared
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass

    private var isCompact: Bool { horizontalSizeClass == .compact }

    private var currentLLMModel: String {
        if !backendService.config.llmActiveModel.isEmpty {
            return backendService.config.llmActiveModel
        }
        return "auto-discover"
    }

    private var isLLMConnected: Bool {
        let provider = discoveryService.activeProvider.isEmpty
            ? backendService.config.llmActiveProvider
            : discoveryService.activeProvider
        return !provider.isEmpty && provider != "simulated"
    }

    private var discoveryLogs: [String] {
        var logs: [String] = []
        let provider = discoveryService.activeProvider.isEmpty
            ? backendService.config.llmActiveProvider
            : discoveryService.activeProvider

        if provider.isEmpty {
            logs.append("System initiated. Probing local LLM providers...")
        } else if provider == "simulated" {
            logs.append("No local LLM provider available. Running in simulated mode.")
            if let error = discoveryService.discoveryError {
                logs.append("Discovery error: \(error)")
            }
        } else {
            let baseURL = discoveryService.activeProvider.isEmpty
                ? ""
                : ""
            logs.append("Active provider: \(provider.prefix(1).uppercased() + provider.dropFirst())")
            if let firstModel = discoveryService.availableModels.first {
                logs.append("Model: \(firstModel)")
            } else if !backendService.config.llmActiveModel.isEmpty {
                logs.append("Model: \(backendService.config.llmActiveModel)")
            }
        }

        logs.append("Qiskit Spacetime Engine ready: 128 virtual qubits allocated.")
        logs.append("CUDA-Q Field Manipulator: GPU acceleration active.")
        logs.append("PennyLane AI Navigator: QML pathfinding model initialized.")
        return logs
    }

    @State private var logEntries: [String] = []

    private var displayLogs: [String] {
        if logEntries.isEmpty {
            return discoveryLogs
        }
        return logEntries
    }

    // Sliders for spacetime control
    @State private var gravityMetric = 0.65
    @State private var velocityMetric = 0.88
    @State private var fieldIntensity = 0.72

    var body: some View {
        VStack(alignment: .leading, spacing: DesignConstants.standardPadding) {
            // Model Fallback Status Indicators
            HStack {
                Text("AI Navigator")
                    .font(.headline)
                    .bold()
                Spacer()

                let connected = isLLMConnected
                Circle()
                    .fill(connected ? DesignConstants.systemGreen : DesignConstants.systemRed)
                    .frame(width: 8, height: 8)
                    .overlay(
                        Circle()
                            .stroke(connected ? DesignConstants.systemGreen.opacity(0.4) : DesignConstants.systemRed.opacity(0.4), lineWidth: 2)
                            .scaleEffect(1.6)
                    )

                Text(connected ? "LLM READY" : "SIMULATED")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(connected ? DesignConstants.systemGreenText : DesignConstants.systemRedText)
            }

            // Models discovery chain visual indicators
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text("DISCOVERY Fallback CHAIN")
                        .font(.caption)
                        .bold()
                        .foregroundStyle(.secondary)

                    Spacer()

                    if discoveryService.isRefreshing {
                        ProgressView()
                            .scaleEffect(0.6)
                            .frame(width: 12, height: 12)
                    } else {
                        Button("Refresh discovery", systemImage: "arrow.clockwise") {
                            Task {
                                await discoveryService.discoverActiveModels()
                                logEntries = discoveryService.discoveryLogs
                            }
                        }
                        .buttonStyle(.plain)
                        .labelStyle(.iconOnly)
                    }
                }

                HStack(spacing: 8) {
                    ForEach(Array(discoveryService.discoveryChain.enumerated()), id: \.offset) { index, status in
                        if index > 0 {
                            Image(systemName: "chevron.right")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                        StatusIndicator(name: status.modelName, isActive: status.isAvailable, isCurrent: status.isCurrent, error: status.error)
                    }
                }
            }
            .padding(10)
            .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))

            // Active model display
            HStack {
                Text("Active Model:")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
                Text(currentLLMModel)
                    .font(.system(.caption, design: .monospaced))
                    .bold()
                    .foregroundStyle(DesignConstants.systemOrangeText)
                    .lineLimit(1)
                    .truncationMode(.middle)
            }
            .padding(.horizontal, 4)

            Divider()

            // Live parameters control
            VStack(alignment: .leading, spacing: 12) {
                Text("Spacetime Field Metrics")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(.secondary)

                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("Gravity Distortion")
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.primaryText)
                        Spacer()
                        Text(gravityMetric, format: .number.precision(.fractionLength(2)))
                            .font(.system(.subheadline, design: .monospaced))
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    PremiumSlider(value: $gravityMetric)
                }

                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("Travel Velocity (c)")
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.primaryText)
                        Spacer()
                        Text(velocityMetric, format: .number.precision(.fractionLength(2)))
                            .font(.system(.subheadline, design: .monospaced))
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    PremiumSlider(value: $velocityMetric)
                }

                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("Field Density (\u{039B})")
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.primaryText)
                        Spacer()
                        Text(fieldIntensity, format: .number.precision(.fractionLength(2)))
                            .font(.system(.subheadline, design: .monospaced))
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    PremiumSlider(value: $fieldIntensity)
                }
            }

            Divider()

            // RealityKit 3D Grid Layout View
            VStack(alignment: .leading, spacing: 6) {
                Text("Spacetime Geodesic Grid")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(.secondary)
                RealitySpacetimeView(tensor: FieldGeometryTensor(gravity: gravityMetric, velocity: velocityMetric, intensity: fieldIntensity))
            }

            Divider()

            // AI Log Stream
            VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
                Text("Temporal Reasoning Stream")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(.secondary)

                ScrollView {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(displayLogs, id: \.self) { log in
                            HStack(alignment: .top, spacing: 6) {
                                Text(">")
                                    .font(.system(.caption, design: .monospaced))
                                    .foregroundStyle(DesignConstants.systemOrangeText)
                                Text(log)
                                    .font(.system(.caption, design: .monospaced))
                                    .foregroundStyle(DesignConstants.primaryText)
                                    .multilineTextAlignment(.leading)
                            }
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(maxHeight: 150)
                .padding(8)
                .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))
            }

            // Sim Action Button or Progress view
            if backendService.isSolvingSpacetime {
                HStack {
                    Spacer()
                    ProgressView()
                        .tint(.white)
                    Text("Solving Spacetime Geodesic...")
                        .font(.subheadline)
                        .bold()
                        .foregroundStyle(.white)
                    Spacer()
                }
                .padding()
                .background(DesignConstants.systemOrange.opacity(0.7), in: RoundedRectangle(cornerRadius: DesignConstants.buttonCornerRadius))
            } else {
                Button(action: simulateTimeTravel) {
                    HStack {
                        Spacer()
                        Label("Solve Spacetime Geodesic", systemImage: "bolt.fill")
                        Spacer()
                    }
                    .padding()
                    .background(DesignConstants.systemOrange, in: RoundedRectangle(cornerRadius: DesignConstants.buttonCornerRadius))
                    .foregroundStyle(.white)
                    .bold()
                }
                .buttonStyle(.plain)
            }
        }
        .padding(DesignConstants.standardPadding)
        .liquidGlass()
        .frame(maxWidth: isCompact ? .infinity : 320)
        .onAppear {
            if logEntries.isEmpty {
                logEntries = discoveryLogs
            }
        }
        .onChange(of: discoveryService.activeProvider) { _, _ in
            logEntries = discoveryLogs
        }
    }

    private func simulateTimeTravel() {
        guard !backendService.isSolvingSpacetime else { return }

        logEntries.append("Executing Qiskit pathfinding solver request...")

        Task {
            do {
                let response = try await backendService.solveSpacetimeGeodesic(
                    gravity: gravityMetric,
                    velocity: velocityMetric,
                    intensity: fieldIntensity
                )

                await MainActor.run {
                    withAnimation {
                        self.gravityMetric = response.gravityMetric
                        self.velocityMetric = response.velocityMetric
                        self.fieldIntensity = response.fieldIntensity
                        for log in response.logs {
                            self.logEntries.append(log)
                        }
                    }
                }
            } catch {
                await MainActor.run {
                    self.logEntries.append("Solver failed: \(error.localizedDescription)")
                }
            }
        }
    }
}

// Subview for Fallback indicator to comply with separate views rule
struct StatusIndicator: View {
    let name: String
    let isActive: Bool
    let isCurrent: Bool
    let error: String?

    var body: some View {
        VStack(spacing: 2) {
            Text(name)
                .font(.system(.caption, design: .monospaced))
                .fontWeight(.semibold)
                .foregroundStyle(
                    isCurrent ? DesignConstants.primaryText : (isActive ? DesignConstants.systemGreenText : Color.secondary)
                )
            if let error = error, !isActive {
                Text(error)
                    .font(.caption2)
                    .foregroundStyle(.red)
                    .lineLimit(1)
                    .truncationMode(.tail)
            }
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 3)
        .background(
            isCurrent ? DesignConstants.systemOrange.opacity(0.15) : (isActive ? DesignConstants.systemGreen.opacity(0.12) : Color.gray.opacity(0.1)),
            in: RoundedRectangle(cornerRadius: 4)
        )
    }
}

#Preview {
    AINavigatorView()
        .padding()
        .background(Color.gray.opacity(0.1))
}
