//
//  AINavigatorView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI

struct AINavigatorView: View {
    @State private var isThinking = false
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
                
                Circle()
                    .fill(isThinking ? DesignConstants.systemOrange : Color.green)
                    .frame(width: 8, height: 8)
                    .scaleEffect(isThinking ? 1.3 : 1.0)
                    .animation(isThinking ? DesignConstants.thinkingAnimation : .default, value: isThinking)
                
                Text(isThinking ? "SOLVING FIELD" : "ON STANDBY")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(isThinking ? DesignConstants.systemOrange : .green)
            }
            
            // Models discovery chain visual indicators
            VStack(alignment: .leading, spacing: 6) {
                Text("DISCOVERY Fallback CHAIN")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(.secondary)
                
                HStack(spacing: 8) {
                    StatusIndicator(name: "oMLX (Mac)", isActive: true, isCurrent: true)
                    Image(systemName: "chevron.right")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    StatusIndicator(name: "Ollama", isActive: true, isCurrent: false)
                    Image(systemName: "chevron.right")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    StatusIndicator(name: "LM Studio", isActive: false, isCurrent: false)
                }
            }
            .padding(10)
            .background(Color.black.opacity(0.04), in: RoundedRectangle(cornerRadius: 8))
            
            Divider()
            
            // Live parameters control
            VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
                Text("Spacetime Field Metrics")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(.secondary)
                
                LabeledContent("Gravity Distortion") {
                    Slider(value: $gravityMetric)
                        .tint(DesignConstants.systemOrange)
                }
                .font(.subheadline)
                
                LabeledContent("Travel Velocity (c)") {
                    Slider(value: $velocityMetric)
                        .tint(DesignConstants.systemOrange)
                }
                .font(.subheadline)
                
                LabeledContent("Field Density (Λ)") {
                    Slider(value: $fieldIntensity)
                        .tint(DesignConstants.systemOrange)
                }
                .font(.subheadline)
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
                                    .foregroundStyle(DesignConstants.systemOrange)
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
                .background(Color.black.opacity(0.03), in: RoundedRectangle(cornerRadius: 8))
            }
            
            // Sim Action Button
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
        .padding(DesignConstants.standardPadding)
        .liquidGlass()
        .frame(maxWidth: 320)
    }
    
    private func simulateTimeTravel() {
        guard !isThinking else { return }
        
        isThinking = true
        logs.append("Executing PennyLane pathfinding optimization...")
        
        // Simulating async progress updates to display real-time calculations
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            logs.append("Qiskit computed Hamiltonian expectation <H> = 0.724")
            gravityMetric = Double.random(in: 0.2...0.9)
            
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                logs.append("Entangled state resolved: CTC is navigable.")
                velocityMetric = Double.random(in: 0.7...0.99)
                
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                    logs.append("Geodesic path found! Confidence: 96.8%")
                    fieldIntensity = Double.random(in: 0.4...0.8)
                    isThinking = false
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
                isCurrent ? DesignConstants.systemOrange.opacity(0.15) : (isActive ? Color.green.opacity(0.12) : Color.gray.opacity(0.1)),
                in: RoundedRectangle(cornerRadius: 4)
            )
            .foregroundStyle(
                isCurrent ? DesignConstants.systemOrange : (isActive ? Color.green : Color.secondary)
            )
    }
}

#Preview {
    AINavigatorView()
        .padding()
        .background(Color.gray.opacity(0.1))
}
