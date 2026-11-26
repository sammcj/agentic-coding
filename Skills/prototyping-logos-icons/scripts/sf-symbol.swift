// Render a macOS SF Symbol to PNG, to show an app's current symbol beside new glyph concepts.
import AppKit

let args = CommandLine.arguments
guard args.count >= 3 else {
    FileHandle.standardError.write("Usage: swift sf-symbol.swift <symbol-name> <out.png> [point-size]\n".data(using: .utf8)!)
    exit(2)
}
let pointSize = args.count > 3 ? CGFloat(Double(args[3]) ?? 64) : 64
guard let symbol = NSImage(systemSymbolName: args[1], accessibilityDescription: nil),
      let image = symbol.withSymbolConfiguration(.init(pointSize: pointSize, weight: .regular))
else {
    FileHandle.standardError.write("No SF Symbol named \(args[1])\n".data(using: .utf8)!)
    exit(1)
}
// Drawn at 2x so it stays sharp when the sheet scales it down.
let rep = NSBitmapImageRep(
    bitmapDataPlanes: nil, pixelsWide: Int(image.size.width * 2), pixelsHigh: Int(image.size.height * 2),
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB,
    bytesPerRow: 0, bitsPerPixel: 0)!
rep.size = image.size
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
image.draw(in: NSRect(origin: .zero, size: image.size))
NSGraphicsContext.restoreGraphicsState()
try rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: args[2]))
print(args[2])
