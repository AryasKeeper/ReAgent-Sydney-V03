/**
 * OpenTelemetry Setup for Frontend
 * Configures metrics, traces, and logs collection
 */

import { Resource } from '@opentelemetry/resources'
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions'
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web'
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { MeterProvider, PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics'
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http'
import { registerInstrumentations } from '@opentelemetry/instrumentation'
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch'
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load'
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction'
import { trace, metrics, DiagConsoleLogger, DiagLogLevel, diag } from '@opentelemetry/api'

// Configuration
const OTEL_ENDPOINT = process.env.NEXT_PUBLIC_OTEL_ENDPOINT || 'http://localhost:4318'
const SERVICE_NAME = 'reagent-frontend'
const SERVICE_VERSION = process.env.NEXT_PUBLIC_VERSION || '1.0.0'
const ENVIRONMENT = process.env.NODE_ENV || 'development'
const REGION = process.env.VERCEL_REGION || 'syd1'

// Enable debug logging in development
if (ENVIRONMENT === 'development') {
  diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.INFO)
}

export class TelemetryService {
  private static instance: TelemetryService
  private resource: Resource
  private tracerProvider: WebTracerProvider
  private meterProvider: MeterProvider
  private isInitialized = false

  private constructor() {
    // Create resource with service information
    this.resource = Resource.default().merge(
      new Resource({
        [SemanticResourceAttributes.SERVICE_NAME]: SERVICE_NAME,
        [SemanticResourceAttributes.SERVICE_VERSION]: SERVICE_VERSION,
        [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: ENVIRONMENT,
        'service.region': REGION,
        'service.framework': 'nextjs',
        'service.framework.version': '15.0.3',
      })
    )

    // Initialize providers
    this.tracerProvider = new WebTracerProvider({
      resource: this.resource,
    })

    this.meterProvider = new MeterProvider({
      resource: this.resource,
    })
  }

  static getInstance(): TelemetryService {
    if (!TelemetryService.instance) {
      TelemetryService.instance = new TelemetryService()
    }
    return TelemetryService.instance
  }

  initialize(): void {
    if (this.isInitialized) {
      console.warn('Telemetry already initialized')
      return
    }

    // Skip initialization in development unless explicitly enabled
    if (ENVIRONMENT === 'development' && !process.env.NEXT_PUBLIC_ENABLE_TELEMETRY) {
      console.log('Telemetry disabled in development')
      return
    }

    try {
      // Configure trace exporter
      const traceExporter = new OTLPTraceExporter({
        url: `${OTEL_ENDPOINT}/v1/traces`,
        headers: {
          'Content-Type': 'application/json',
        },
      })

      // Add span processor
      this.tracerProvider.addSpanProcessor(
        new BatchSpanProcessor(traceExporter, {
          maxQueueSize: 100,
          maxExportBatchSize: 10,
          scheduledDelayMillis: 500,
        })
      )

      // Configure metric exporter
      const metricExporter = new OTLPMetricExporter({
        url: `${OTEL_ENDPOINT}/v1/metrics`,
        headers: {
          'Content-Type': 'application/json',
        },
      })

      // Add metric reader
      this.meterProvider.addMetricReader(
        new PeriodicExportingMetricReader({
          exporter: metricExporter,
          exportIntervalMillis: 30000, // 30 seconds
        })
      )

      // Register providers globally
      trace.setGlobalTracerProvider(this.tracerProvider)
      metrics.setGlobalMeterProvider(this.meterProvider)

      // Register auto-instrumentations
      registerInstrumentations({
        instrumentations: [
          new FetchInstrumentation({
            propagateTraceHeaderCorsUrls: [
              /localhost:8001/,
              /reagent-backend/,
            ],
            clearTimingResources: true,
            applyCustomAttributesOnSpan: (span, request, response) => {
              // Add custom attributes to fetch spans
              span.setAttribute('http.request.body.size', request.headers.get('content-length') || 0)
              if (response) {
                span.setAttribute('http.response.body.size', response.headers.get('content-length') || 0)
              }
            },
          }),
          new DocumentLoadInstrumentation(),
          new UserInteractionInstrumentation({
            eventNames: ['click', 'submit', 'change'],
          }),
        ],
      })

      this.isInitialized = true
      console.log('Telemetry initialized successfully')
    } catch (error) {
      console.error('Failed to initialize telemetry:', error)
    }
  }

  shutdown(): Promise<void> {
    return Promise.all([
      this.tracerProvider.shutdown(),
      this.meterProvider.shutdown(),
    ]).then(() => {
      console.log('Telemetry shut down successfully')
    })
  }

  getTracer(name: string = SERVICE_NAME) {
    return trace.getTracer(name, SERVICE_VERSION)
  }

  getMeter(name: string = SERVICE_NAME) {
    return metrics.getMeter(name, SERVICE_VERSION)
  }
}

// Initialize telemetry on module load
if (typeof window !== 'undefined') {
  const telemetry = TelemetryService.getInstance()
  telemetry.initialize()

  // Graceful shutdown on page unload
  window.addEventListener('beforeunload', () => {
    telemetry.shutdown()
  })
}

export default TelemetryService.getInstance()