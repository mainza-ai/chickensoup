//
//  RealitySpacetimeView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import SwiftUI
#if canImport(RealityKit)
import RealityKit
#endif

#if os(macOS)
import AppKit
typealias ViewRepresentable = NSViewRepresentable
#else
import UIKit
typealias ViewRepresentable = UIViewRepresentable
#endif

// Represents the tensor field geometry parameters
public struct FieldGeometryTensor: Sendable {
    public var gravity: Double
    public var velocity: Double
    public var intensity: Double
    
    public init(gravity: Double, velocity: Double, intensity: Double) {
        self.gravity = gravity
        self.velocity = velocity
        self.intensity = intensity
    }
}

struct RealitySpacetimeView: View {
    let tensor: FieldGeometryTensor
    
    var body: some View {
        SpacetimeCanvasFallback(tensor: tensor)
    }
}

#if canImport(RealityKit) && !targetEnvironment(simulator)
struct RealitySpacetimeARViewContainer: ViewRepresentable {
    let tensor: FieldGeometryTensor
    
    #if os(macOS)
    func makeNSView(context: Context) -> ARView {
        let arView = ARView(frame: .zero)
        setupScene(arView: arView)
        return arView
    }
    
    func updateNSView(_ nsView: ARView, context: Context) {
        updateGrid(arView: nsView)
    }
    #else
    func makeUIView(context: Context) -> ARView {
        #if os(iOS)
        let arView = ARView(frame: .zero, cameraMode: .nonAR, automaticallyConfigureSession: false)
        #else
        let arView = ARView(frame: .zero)
        #endif
        setupScene(arView: arView)
        return arView
    }
    
    func updateUIView(_ uiView: ARView, context: Context) {
        updateGrid(arView: uiView)
    }
    #endif
    
    private func setupScene(arView: ARView) {
        // Clear background
        arView.environment.background = .color(.clear)
        
        // Add a simple camera entity
        let cameraEntity = PerspectiveCamera()
        cameraEntity.camera.fieldOfViewInDegrees = 60
        
        let cameraAnchor = AnchorEntity(world: .zero)
        cameraAnchor.addChild(cameraEntity)
        arView.scene.addAnchor(cameraAnchor)
        
        // Position camera
        cameraEntity.position = [0, 1.5, 3.0]
        cameraEntity.look(at: [0, 0, 0], from: cameraEntity.position, relativeTo: nil)
        
        // Create grid anchor
        let gridAnchor = AnchorEntity(world: .zero)
        gridAnchor.name = "GridAnchor"
        arView.scene.addAnchor(gridAnchor)
    }
    
    private func updateGrid(arView: ARView) {
        guard let gridAnchor = arView.scene.anchors.first(where: { $0.name == "GridAnchor" }) else { return }
        
        // Remove existing grid children
        gridAnchor.children.removeAll()
        
        // Build the curved 3D grid layout based on FieldGeometryTensor
        let gridSize = 11
        let step: Float = 0.15
        let offset = Float(gridSize - 1) * step / 2.0
        
        let sphereMesh = MeshResource.generateSphere(radius: 0.015)
        let material = SimpleMaterial(color: .systemOrange, isMetallic: true)
        
        for x in 0..<gridSize {
            for y in 0..<gridSize {
                let posX = Float(x) * step - offset
                let posZ = Float(y) * step - offset
                
                // Calculate curved Y coordinate from FieldGeometryTensor
                let dx = Double(posX)
                let dz = Double(posZ)
                let dist = sqrt(dx*dx + dz*dz)
                let baseCurvature = tensor.gravity * 0.4 / (1.0 + dist * dist)
                let waveCurvature = sin(dist * 6.0 - tensor.velocity * 8.0) * tensor.intensity * 0.08
                let posY = Float(baseCurvature + waveCurvature)
                
                let model = ModelEntity(mesh: sphereMesh, materials: [material])
                model.position = [posX, posY - 0.2, posZ]
                gridAnchor.addChild(model)
            }
        }
    }
}
#endif

// High-fidelity fallback renderer using SwiftUI Canvas and 3D Perspective Projection
struct SpacetimeCanvasFallback: View {
    let tensor: FieldGeometryTensor
    
    var body: some View {
        SwiftUI.TimelineView(.animation) { timeline in
            Canvas { context, size in
                let time = timeline.date.timeIntervalSinceReferenceDate
                drawGrid(context: context, size: size, time: time)
            }
        }
        .frame(height: 180)
        .background(Color.black.opacity(0.05))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
    }
    
    private func drawGrid(context: GraphicsContext, size: CGSize, time: Double) {
        let centerX = Double(size.width / 2)
        let centerY = Double(size.height / 2)
        
        let count = 15
        let spacing: Double = 16.0
        let halfWidth = Double(count - 1) * spacing / 2.0
        
        context.stroke(
            Path { path in
                for i in 0..<count {
                    let xo = Double(i) * spacing - halfWidth
                    var lastPoint: CGPoint? = nil
                    
                    for j in 0..<count {
                        let zo = Double(j) * spacing - halfWidth
                        
                        // Clean math calculations entirely in Double to prevent type checker overhead
                        let dx = xo / 100.0
                        let dz = zo / 100.0
                        let dist = sqrt(dx * dx + dz * dz)
                        
                        let gravityWell = (tensor.gravity * 60.0) / (1.0 + dist * dist * 3.0)
                        let wave = sin(dist * 5.0 - tensor.velocity * time * 5.0) * tensor.intensity * 15.0
                        let dy = gravityWell + wave
                        
                        let projZ = 200.0 + zo
                        let scale = 200.0 / projZ
                        
                        let px = centerX + (xo * scale)
                        let py = centerY + (dy * scale) + (zo * 0.3 * scale)
                        
                        let currentPoint = CGPoint(x: px, y: py)
                        if let prev = lastPoint {
                            path.move(to: prev)
                            path.addLine(to: currentPoint)
                        }
                        lastPoint = currentPoint
                    }
                }
                
                for j in 0..<count {
                    let zo = Double(j) * spacing - halfWidth
                    var lastPoint: CGPoint? = nil
                    
                    for i in 0..<count {
                        let xo = Double(i) * spacing - halfWidth
                        
                        let dx = xo / 100.0
                        let dz = zo / 100.0
                        let dist = sqrt(dx * dx + dz * dz)
                        
                        let gravityWell = (tensor.gravity * 60.0) / (1.0 + dist * dist * 3.0)
                        let wave = sin(dist * 5.0 - tensor.velocity * time * 5.0) * tensor.intensity * 15.0
                        let dy = gravityWell + wave
                        
                        let projZ = 200.0 + zo
                        let scale = 200.0 / projZ
                        
                        let px = centerX + (xo * scale)
                        let py = centerY + (dy * scale) + (zo * 0.3 * scale)
                        
                        let currentPoint = CGPoint(x: px, y: py)
                        if let prev = lastPoint {
                            path.move(to: prev)
                            path.addLine(to: currentPoint)
                        }
                        lastPoint = currentPoint
                    }
                }
            },
            with: .color(Color.orange.opacity(0.45)),
            lineWidth: 1.0
        )
        
        // Draw primary gravity center singularity
        let pulse = 8.0 + sin(time * 3.0) * 2.0
        context.fill(
            Path(ellipseIn: CGRect(x: CGFloat(centerX - pulse), y: CGFloat(centerY - pulse), width: CGFloat(pulse * 2.0), height: CGFloat(pulse * 2.0))),
            with: .radialGradient(
                Gradient(colors: [.orange, .red.opacity(0.1), .clear]),
                center: CGPoint(x: CGFloat(centerX), y: CGFloat(centerY)),
                startRadius: 0,
                endRadius: CGFloat(pulse * 2.5)
            )
        )
    }
}

#Preview {
    RealitySpacetimeView(tensor: FieldGeometryTensor(gravity: 0.65, velocity: 0.88, intensity: 0.72))
        .padding()
}
