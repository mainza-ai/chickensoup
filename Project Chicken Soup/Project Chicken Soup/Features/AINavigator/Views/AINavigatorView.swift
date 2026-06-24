//
//  AINavigatorView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI

struct AINavigatorView: View {
    @ObservedObject var discoveryService = LLMDiscoveryService.shared
    @ObservedObject var backendService = BackendService.shared
    
    @State private var logs: [String] = [
        "System initiated. Connecting local LLM...",
        "oMLX discoverable at 127.0.0.1:9000. Fallbacks loaded.",
        "Qiskit Spacetime Engine ready: 128 virtual qubits allocated.",
        "CUDA-Q Field Manipulator: GPU acceleration active.",
        "PennyLane AI Navigator: QML pathfinding model initialized."
    ]
    
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
                
                let isThinking = backendService.isSolvingSpacetime
                Circle()
                    .fill(isThinking ? DesignConstants.systemOrange : DesignConstants.systemGreen)
                    .frame(width: 8, height: 8)
                    .scaleEffect(isThinking ? 1.3 : 1.0)
                    .animation(isThinking ? DesignConstants.thinkingAnimation : .default, value: isThinking)
                
                Text(isThinking ? "SOLVING FIELD" : "ON STANDBY")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(isThinking ? DesignConstants.systemOrangeText : DesignConstants.systemGreenText)
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
                        Button {
                            Task {
                                await discoveryService.discoverActiveModels()
                            }
                        } label: {
                            Image(systemName: "arrow.clockwise")
                                .font(.caption2)
                                .foregroundStyle(DesignConstants.systemOrangeText)
                        }
                        .buttonStyle(.plain)
                    }
                }
                
                HStack(spacing: 8) {
                    ForEach(Array(discoveryService.discoveryChain.enumerated()), id: \.offset) { index, status in
                        if index > 0 {
                            Image(systemName: "chevron.right")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                        StatusIndicator(name: status.modelName, isActive: status.isAvailable, isCurrent: status.isCurrent)
                    }
                }
            }
            .padding(10)
            .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))
            
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
                        Text(String(format: "%.2f", gravityMetric))
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
                        Text(String(format: "%.2f", velocityMetric))
                            .font(.system(.subheadline, design: .monospaced))
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    PremiumSlider(value: $velocityMetric)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("Field Density (Λ)")
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.primaryText)
                        Spacer()
                        Text(String(format: "%.2f", fieldIntensity))
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
                        ForEach(logs, id: \.self) { log in
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
        .frame(maxWidth: 320)
    }
    
    private func simulateTimeTravel() {
        guard !backendService.isSolvingSpacetime else { return }
        
        logs.append("Executing Qiskit pathfinding solver request...")
        
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
                            self.logs.append(log)
                        }
                    }
                }
            } catch {
                await MainActor.run {
                    self.logs.append("Solver failed: \(error.localizedDescription)")
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
    
    var body: some View {
        Text(name)
            .font(.system(size: 9, weight: .semibold, design: .monospaced))
            .padding(.horizontal, 6)
            .padding(.vertical, 3)
            .background(
                isCurrent ? DesignConstants.systemOrange.opacity(0.15) : (isActive ? DesignConstants.systemGreen.opacity(0.12) : Color.gray.opacity(0.1)),
                in: RoundedRectangle(cornerRadius: 4)
            )
            .foregroundStyle(
                isCurrent ? DesignConstants.primaryText : (isActive ? DesignConstants.systemGreenText : Color.secondary)
            )
    }
}

#Preview {
    AINavigatorView()
        .padding()
        .background(Color.gray.opacity(0.1))
}
