# Shopware 6.7 - Kompletter Entwickler-Guide

> **Version**: 6.7.x | **Datum**: 2026-02-18 | **Projekt**: Netgrade Demo Umgebung

---

## 📋 Inhaltsverzeichnis

1. [Systemanforderungen](#1-systemanforderungen)
2. [Architektur-Überblick](#2-architektur-überblick)
3. [Plugin-Entwicklung](#3-plugin-entwicklung)
4. [DAL (Data Abstraction Layer)](#4-dal-data-abstraction-layer)
5. [Storefront (Frontend)](#5-storefront-frontend)
6. [Administration (Backend)](#6-administration-backend)
7. [CMS Elemente & Blöcke](#7-cms-elemente--blöcke)
8. [Events & Subscriber](#8-events--subscriber)
9. [Migrations & Entities](#9-migrations--entities)
10. [Shopware 6.7 Breaking Changes](#10-shopware-67-breaking-changes)
11. [Nützliche Commands](#11-nützliche-commands)
12. [Weiterführende Links](#12-weiterführende-links)
13. [Storefront Assets Build-Prozess](#13-storefront-assets-build-prozess-shopware-67)
14. [Praktische Learnings & Best Practices](#14-praktische-learnings--best-practices-session-notizen)
    - 14.4 Composer vs. custom/plugins
    - 14.5 Null-Safe in Twig-Templates
    - 14.6 FormCmsHandler Konflikte
    - 14.7 Step-Indikator Scope-Problem
    - 14.8 Step-Farben korrekt definieren
    - 14.9 node_modules in .gitignore
    - 14.20 Plugin-Icon nach Änderung sichtbar machen
    - 14.21 Mail-Templates: Migration für bestehende Installationen
    - 14.22 Mail-Template-Terminologie

---

## 1. Systemanforderungen

| Komponente | Version | Hinweise |
|------------|---------|----------|
| **PHP** | 8.2 - 8.4 | PHP 8.2 ist Minimum |
| **Node.js** | 20+ | Für Admin-Builds |
| **MySQL** | 8.0.17+ | Vermeide 8.0.20, 8.0.21 |
| **MariaDB** | 10.11+ | Vermeide 10.11.5, 11.0.3 |
| **Symfony** | 7.x | |
| **Redis** | 7.0+ | Optional |
| **PHPUnit** | 11.x | Für Tests |

---

## 2. Architektur-Überblick

### 2.1 Verzeichnisstruktur

```
src/
├── Core/                    # Framework-Grundlage
│   ├── Framework/           # Events, DAL, Context, DI
│   ├── System/              # SystemConfig, SalesChannel
│   ├── Content/             # Product, Category, CMS, Media
│   └── Checkout/            # Cart, Order, Payment, Shipping
├── Storefront/              # Frontend (Twig, JS, SCSS)
│   ├── Controller/
│   ├── Resources/views/     # Twig-Templates
│   └── Theme/               # Theme-System
├── Administration/          # Vue.js 3 Admin-Interface
│   └── Resources/app/administration/
└── Elasticsearch/           # Search-Integration
```

### 2.2 Plugin-Struktur

```
NetgradeExamplePlugin/
├── composer.json
├── src/
│   ├── NetgradeExamplePlugin.php      # Plugin-Basisklasse
│   ├── Controller/
│   │   ├── Administration/
│   │   └── Storefront/
│   ├── Core/
│   │   └── Content/
│   │       └── Example/
│   │           ├── ExampleDefinition.php
│   │           ├── ExampleEntity.php
│   │           └── ExampleCollection.php
│   ├── Migration/
│   ├── Resources/
│   │   ├── config/
│   │   │   ├── services.xml
│   │   │   └── config.xml
│   │   ├── app/
│   │   │   ├── administration/
│   │   │   │   └── src/
│   │   │   │       ├── main.js
│   │   │   │       └── module/
│   │   │   └── storefront/
│   │   │       └── src/
│   │   │           ├── main.js
│   │   │           ├── scss/
│   │   │           └── js/
│   │   └── views/
│   ├── Service/
│   └── Subscriber/
└── tests/
```

---

## 3. Plugin-Entwicklung

### 3.1 composer.json Template

```json
{
    "name": "netgrade/example-plugin",
    "description": "Example plugin for Shopware 6.7",
    "version": "1.0.0",
    "type": "shopware-platform-plugin",
    "license": "MIT",
    "authors": [
        {
            "name": "Netgrade GmbH",
            "homepage": "https://netgrade.de/"
        }
    ],
    "require": {
        "shopware/core": "~6.7.0",
        "shopware/storefront": "~6.7.0",
        "shopware/administration": "~6.7.0"
    },
    "extra": {
        "shopware-plugin-class": "Netgrade\\ExamplePlugin\\NetgradeExamplePlugin",
        "plugin-icon": "src/Resources/config/netgrade-shopware-plugin-icon.png",
        "label": {
            "de-DE": "Netgrade Example Plugin",
            "en-GB": "Netgrade Example Plugin"
        },
        "description": {
            "de-DE": "Beschreibung auf Deutsch",
            "en-GB": "Description in English"
        }
    },
    "autoload": {
        "psr-4": {
            "Netgrade\\ExamplePlugin\\": "src/"
        }
    }
}
```

### 3.2 Plugin-Basisklasse

```php
<?php declare(strict_types=1);

namespace Netgrade\ExamplePlugin;

use Shopware\Core\Framework\Plugin;
use Shopware\Core\Framework\Plugin\Context\InstallContext;
use Shopware\Core\Framework\Plugin\Context\UninstallContext;

class NetgradeExamplePlugin extends Plugin
{
    public function install(InstallContext $installContext): void
    {
        parent::install($installContext);
        // Install-Logik
    }

    public function uninstall(UninstallContext $uninstallContext): void
    {
        parent::uninstall($uninstallContext);
        
        if ($uninstallContext->keepUserData()) {
            return;
        }
        // Cleanup-Logik
    }
    
    public function getMigrationNamespace(): string
    {
        return 'Netgrade\ExamplePlugin\Migration';
    }
}
```

### 3.3 services.xml (DI-Konfiguration)

```xml
<?xml version="1.0" ?>
<container xmlns="http://symfony.com/schema/dic/services"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://symfony.com/schema/dic/services http://symfony.com/schema/dic/services/services-1.0.xsd">
    <services>
        <!-- Autowiring & Autoconfigure -->
        <defaults autowire="true" autoconfigure="true"/>

        <!-- Prototype-Registrierung für alle Services im src/ Ordner -->
        <prototype namespace="Netgrade\ExamplePlugin\" resource="../../" exclude="../../{Resources,Migration,*.php}"/>

        <!-- Manuelle Service-Definition (falls nötig) -->
        <service id="Netgrade\ExamplePlugin\Service\CustomService">
            <argument type="service" id="product.repository"/>
        </service>

        <!-- Event Subscriber -->
        <service id="Netgrade\ExamplePlugin\Subscriber\ProductSubscriber">
            <tag name="kernel.event_subscriber"/>
        </service>

        <!-- Console Command -->
        <service id="Netgrade\ExamplePlugin\Command\CustomCommand">
            <tag name="console.command"/>
        </service>

        <!-- Scheduled Task -->
        <service id="Netgrade\ExamplePlugin\ScheduledTask\CustomTask">
            <tag name="shopware.scheduled.task"/>
        </service>
        
        <service id="Netgrade\ExamplePlugin\ScheduledTask\CustomTaskHandler">
            <argument type="service" id="scheduled_task.repository"/>
            <tag name="messenger.message_handler"/>
        </service>
    </services>
</container>
```

---

## 4. DAL (Data Abstraction Layer)

### 4.1 Repository-Pattern

```php
<?php declare(strict_types=1);

namespace Netgrade\ExamplePlugin\Service;

use Shopware\Core\Framework\DataAbstractionLayer\EntityRepository;
use Shopware\Core\Framework\DataAbstractionLayer\Search\Criteria;
use Shopware\Core\Framework\DataAbstractionLayer\Search\Filter\EqualsFilter;
use Shopware\Core\Framework\DataAbstractionLayer\Search\Filter\ContainsFilter;
use Shopware\Core\Framework\DataAbstractionLayer\Search\Filter\RangeFilter;
use Shopware\Core\Framework\DataAbstractionLayer\Search\Sorting\FieldSorting;
use Shopware\Core\Framework\Context;

class ProductService
{
    public function __construct(
        private EntityRepository $productRepository
    ) {}

    // READ - Einzelnes Produkt
    public function getProduct(string $id, Context $context): ?ProductEntity
    {
        $criteria = new Criteria([$id]);
        $criteria->addAssociation('media');
        $criteria->addAssociation('categories');
        
        return $this->productRepository->search($criteria, $context)->first();
    }

    // READ - Suche mit Filtern
    public function findActiveProducts(Context $context): EntitySearchResult
    {
        $criteria = new Criteria();
        $criteria->addFilter(new EqualsFilter('active', true));
        $criteria->addSorting(new FieldSorting('createdAt', FieldSorting::DESCENDING));
        $criteria->setLimit(25);
        
        return $this->productRepository->search($criteria, $context);
    }

    // CREATE
    public function createProduct(array $data, Context $context): void
    {
        $this->productRepository->create([
            [
                'id' => Uuid::randomHex(),
                'name' => $data['name'],
                'productNumber' => $data['productNumber'],
                'stock' => $data['stock'],
                'taxId' => $data['taxId'],
                'price' => [
                    [
                        'currencyId' => Defaults::CURRENCY,
                        'gross' => $data['priceGross'],
                        'net' => $data['priceNet'],
                        'linked' => false
                    ]
                ],
            ]
        ], $context);
    }

    // UPDATE
    public function updateProduct(string $id, array $data, Context $context): void
    {
        $this->productRepository->update([
            ['id' => $id, 'name' => $data['name']]
        ], $context);
    }

    // UPSERT (Update oder Insert)
    public function upsertProduct(array $data, Context $context): void
    {
        $this->productRepository->upsert([$data], $context);
    }

    // DELETE
    public function deleteProduct(string $id, Context $context): void
    {
        $this->productRepository->delete([['id' => $id]], $context);
    }
}
```

### 4.2 Criteria - Erweiterte Verwendung

```php
use Shopware\Core\Framework\DataAbstractionLayer\Search\Filter\OrFilter;
use Shopware\Core\Framework\DataAbstractionLayer\Search\Filter\AndFilter;
use Shopware\Core\Framework\DataAbstractionLayer\Search\Filter\NotFilter;
use Shopware\Core\Framework\DataAbstractionLayer\Search\Filter\MultiFilter;
use Shopware\Core\Framework\DataAbstractionLayer\Search\Aggregation\Metric\AvgAggregation;
use Shopware\Core\Framework\DataAbstractionLayer\Search\Aggregation\Metric\MaxAggregation;
use Shopware\Core\Framework\DataAbstractionLayer\Search\Aggregation\Metric\CountAggregation;

$criteria = new Criteria();

// Verschachtelte Filter
$criteria->addFilter(new AndFilter([
    new EqualsFilter('active', true),
    new OrFilter([
        new RangeFilter('stock', [RangeFilter::GT => 0]),
        new EqualsFilter('isCloseout', false)
    ])
]));

// Post-Filter (beeinflussen Aggregationen nicht)
$criteria->addPostFilter(new EqualsFilter('active', true));

// Association mit Filter
$criteria->getAssociation('reviews')
    ->addFilter(new RangeFilter('points', [RangeFilter::GTE => 4]))
    ->addSorting(new FieldSorting('createdAt', FieldSorting::DESCENDING))
    ->setLimit(5);

// Aggregationen
$criteria->addAggregation(new AvgAggregation('avg-rating', 'reviews.points'));
$criteria->addAggregation(new MaxAggregation('max-price', 'price'));
$criteria->addAggregation(new CountAggregation('review-count', 'reviews.id'));

// Full-Text Search
$criteria->setTerm('suchbegriff');

// Pagination
$criteria->setLimit(25);
$criteria->setOffset(50);
```

---

## 5. Storefront (Frontend)

### 5.1 Controller mit PHP 8 Attributen

```php
<?php declare(strict_types=1);

namespace Netgrade\ExamplePlugin\Controller\Storefront;

use Shopware\Core\System\SalesChannel\SalesChannelContext;
use Shopware\Storefront\Controller\StorefrontController;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;
use Shopware\Core\PlatformRequest;
use Shopware\Storefront\Framework\Routing\StorefrontRouteScope;

#[Route(defaults: [PlatformRequest::ATTRIBUTE_ROUTE_SCOPE => [StorefrontRouteScope::ID]])]
class ExampleController extends StorefrontController
{
    #[Route(path: '/example', name: 'frontend.example.example', methods: ['GET'])]
    public function showExample(SalesChannelContext $context): Response
    {
        return $this->renderStorefront('@NetgradeExamplePlugin/storefront/page/example.html.twig', [
            'pageTitle' => 'Example Page'
        ]);
    }

    #[Route(path: '/example/form', name: 'frontend.example.form', methods: ['POST'])]
    public function handleForm(Request $request, SalesChannelContext $context): Response
    {
        $formData = $request->request->all();
        
        // Verarbeitung...
        
        $this->addFlash('success', 'Form submitted successfully');
        
        return $this->redirectToRoute('frontend.example.example');
    }
}
```

### 5.2 routes.xml

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<routes xmlns="http://symfony.com/schema/routing"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://symfony.com/schema/routing
        https://symfony.com/schema/routing/routing-1.0.xsd">

    <import resource="Netgrade\ExamplePlugin\Controller\Storefront\ExampleController" type="attribute" />
</routes>
```

### 5.3 Twig-Templates

```twig
{# @NetgradeExamplePlugin/storefront/page/example.html.twig #}
{% sw_extends '@Storefront/storefront/page/content/index.html.twig' %}

{% block base_content %}
    {{ parent() }}
    
    <div class="netgrade-example-container">
        <h1>{{ pageTitle }}</h1>
        
        {# Flash Messages #}
        {% for type, messages in app.flashes %}
            {% for message in messages %}
                <div class="alert alert-{{ type }}">
                    {{ message }}
                </div>
            {% endfor %}
        {% endfor %}
        
        {# Formular #}
        <form action="{{ path('frontend.example.form') }}" method="post">
            {{ csrf_field() }}
            
            <div class="form-group">
                <label for="name">Name</label>
                <input type="text" id="name" name="name" class="form-control" required>
            </div>
            
            <button type="submit" class="btn btn-primary">Submit</button>
        </form>
    </div>
{% endblock %}
```

### 5.4 JavaScript-Plugins

```javascript
// src/Resources/app/storefront/src/example-plugin/example-plugin.plugin.js
const { PluginBaseClass } = window;

export default class ExamplePlugin extends PluginBaseClass {
    static options = {
        delay: 500,
        selector: '.my-element'
    };

    init() {
        this._registerEvents();
    }
    
    _registerEvents() {
        window.addEventListener('scroll', this._onScroll.bind(this));
        this.el.addEventListener('click', this._onClick.bind(this));
    }
    
    _onScroll() {
        // Scroll-Logik
    }
    
    _onClick(event) {
        event.preventDefault();
        // Click-Logik
    }
}
```

```javascript
// src/Resources/app/storefront/src/main.js
import ExamplePlugin from './example-plugin/example-plugin.plugin';

const PluginManager = window.PluginManager;

// Basis-Registrierung
PluginManager.register('ExamplePlugin', ExamplePlugin);

// Mit DOM-Selector
PluginManager.register('ExamplePlugin', ExamplePlugin, '[data-example-plugin]');

// Lazy Loading (für große Plugins)
PluginManager.register('HeavyPlugin', () => import('./heavy-plugin/heavy-plugin.plugin'), '[data-heavy-plugin]');
```

### 5.5 Template-Integration

```twig
{# Daten-Attribute für JS-Plugin #}
<div data-example-plugin
     data-example-plugin-options='{"delay": 1000}'>
    Content
</div>
```

---

## 6. Administration (Backend)

### 6.1 main.js Entry Point

```javascript
// src/Resources/app/administration/src/main.js
import './module/netgrade-example';
```

### 6.2 Modul-Registrierung

```javascript
// src/Resources/app/administration/src/module/netgrade-example/index.js
import './page/example-list';
import './page/example-detail';

import deDE from './snippet/de-DE.json';
import enGB from './snippet/en-GB.json';

Shopware.Module.register('netgrade-example', {
    type: 'plugin',
    name: 'NetgradeExample',
    title: 'netgrade-example.general.mainMenuItemGeneral',
    description: 'netgrade-example.general.description',
    color: '#ff6b35',
    icon: 'regular-shopping-bag',
    entity: 'netgrade_example',

    snippets: {
        'de-DE': deDE,
        'en-GB': enGB
    },

    routes: {
        list: {
            component: 'netgrade-example-list',
            path: 'list'
        },
        detail: {
            component: 'netgrade-example-detail',
            path: 'detail/:id',
            meta: {
                parentPath: 'netgrade.example.list'
            }
        },
        create: {
            component: 'netgrade-example-detail',
            path: 'create',
            meta: {
                parentPath: 'netgrade.example.list'
            }
        }
    },

    navigation: [{
        id: 'netgrade-example',
        path: 'netgrade.example.list',
        label: 'netgrade-example.general.mainMenuItemGeneral',
        icon: 'regular-shopping-bag',
        position: 100,
        parent: 'sw-marketing'  // oder: sw-catalogue, sw-content, sw-settings
    }]
});
```

### 6.3 Meteor Components (Shopware 6.7+)

| Alt (sw-*) | Neu (mt-*) |
|------------|------------|
| `sw-button` | `mt-button` |
| `sw-card` | `mt-card` |
| `sw-text-field` | `mt-text-field` |
| `sw-textarea-field` | `mt-textarea` |
| `sw-select-field` | `mt-select` |
| `sw-switch-field` | `mt-switch` |
| `sw-checkbox-field` | `mt-checkbox` |
| `sw-datepicker` | `mt-datepicker` |
| `sw-icon` | `mt-icon` |
| `sw-modal` | `mt-modal` |

### 6.4 Komponente mit Pinia (6.7+)

```javascript
// src/Resources/app/administration/src/module/netgrade-example/page/example-list/index.js
import template from './example-list.html.twig';

const { Component } = Shopware;
const { Criteria } = Shopware.Data;

Component.register('netgrade-example-list', {
    template,

    inject: ['repositoryFactory'],

    data() {
        return {
            items: [],
            isLoading: false,
            sortBy: 'createdAt',
            sortDirection: 'DESC'
        };
    },

    computed: {
        repository() {
            return this.repositoryFactory.create('netgrade_example');
        },

        columns() {
            return [
                {
                    property: 'name',
                    label: this.$tc('netgrade-example.list.columnName'),
                    primary: true
                },
                {
                    property: 'active',
                    label: this.$tc('netgrade-example.list.columnActive')
                },
                {
                    property: 'createdAt',
                    label: this.$tc('netgrade-example.list.columnCreatedAt')
                }
            ];
        }
    },

    created() {
        this.getList();
    },

    methods: {
        async getList() {
            this.isLoading = true;
            
            const criteria = new Criteria();
            criteria.addSorting(Criteria.sort(this.sortBy, this.sortDirection));
            
            try {
                const result = await this.repository.search(
                    criteria,
                    Shopware.Context.api
                );
                this.items = result;
            } finally {
                this.isLoading = false;
            }
        }
    }
});
```

```twig
{# example-list.html.twig #}
<sw-page class="netgrade-example-list">
    <template #smart-bar-header>
        <h2>{{ $tc('netgrade-example.list.title') }}</h2>
    </template>

    <template #smart-bar-actions>
        <mt-button variant="primary" @click="$router.push({ name: 'netgrade.example.create' })">
            {{ $tc('netgrade-example.list.buttonCreate') }}
        </mt-button>
    </template>

    <template #content>
        <sw-entity-listing
            v-if="items"
            :items="items"
            :columns="columns"
            :repository="repository"
            :is-loading="isLoading"
            detail-route="netgrade.example.detail">
        </sw-entity-listing>
    </template>
</sw-page>
```

### 6.5 Snippets (Übersetzungen)

```json
{
    "netgrade-example": {
        "general": {
            "mainMenuItemGeneral": "Example Module",
            "description": "Manage example items"
        },
        "list": {
            "title": "Example Items",
            "buttonCreate": "Create",
            "columnName": "Name",
            "columnActive": "Active",
            "columnCreatedAt": "Created At"
        },
        "detail": {
            "title": "Example Detail",
            "cardGeneral": "General"
        }
    }
}
```

---

## 7. CMS Elemente & Blöcke

### 7.1 CMS Element registrieren

```javascript
// src/Resources/app/administration/src/module/sw-cms/elements/netgrade-custom/index.js
import './component';
import './config';
import './preview';

Shopware.Service('cmsService').registerCmsElement({
    name: 'netgrade-custom',
    label: 'sw-cms.elements.netgradeCustom.label',
    component: 'sw-cms-el-netgrade-custom',
    configComponent: 'sw-cms-el-config-netgrade-custom',
    previewComponent: 'sw-cms-el-preview-netgrade-custom',
    defaultConfig: {
        headline: {
            source: 'static',
            value: 'Default Headline'
        },
        content: {
            source: 'static',
            value: ''
        }
    }
});
```

### 7.2 Storefront Template für CMS Element

```twig
{# src/Resources/views/storefront/element/cms-element-netgrade-custom.html.twig #}
{% block element_netgrade_custom %}
    <div class="cms-element-netgrade-custom">
        <h2>{{ element.config.headline.value }}</h2>
        <div class="content">
            {{ element.config.content.value|raw }}
        </div>
    </div>
{% endblock %}
```

---

## 8. Events & Subscriber

### 8.1 Event Subscriber

```php
<?php declare(strict_types=1);

namespace Netgrade\ExamplePlugin\Subscriber;

use Shopware\Core\Content\Product\ProductEvents;
use Shopware\Core\Framework\DataAbstractionLayer\Event\EntityLoadedEvent;
use Shopware\Core\Framework\DataAbstractionLayer\Event\EntityWrittenEvent;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;

class ProductSubscriber implements EventSubscriberInterface
{
    public static function getSubscribedEvents(): array
    {
        return [
            ProductEvents::PRODUCT_LOADED_EVENT => 'onProductsLoaded',
            ProductEvents::PRODUCT_WRITTEN_EVENT => 'onProductsWritten',
            'checkout.order.placed' => 'onOrderPlaced',
        ];
    }

    public function onProductsLoaded(EntityLoadedEvent $event): void
    {
        foreach ($event->getEntities() as $product) {
            // Produkt-Logik
        }
    }

    public function onProductsWritten(EntityWrittenEvent $event): void
    {
        if ($event->getContext()->getVersionId() !== Defaults::LIVE_VERSION) {
            return;
        }
        
        foreach ($event->getIds() as $id) {
            // Verarbeitung
        }
    }

    public function onOrderPlaced(OrderPlacedEvent $event): void
    {
        $order = $event->getOrder();
        $context = $event->getContext();
        
        // Order-Logik
    }
}
```

### 8.2 Route-spezifische Events (6.6.11+)

```
{route}.request      // Vor Controller
{route}.response     // Nach Controller
{route}.render       // Vor Twig-Rendering
{route}.encode       // Vor JSON-Encoding (Store-API)
{route}.controller   // Controller-Event

Beispiele:
- store-api.product.listing.request
- frontend.checkout.cart.response
```

---

## 9. Migrations & Entities

### 9.1 Entity Definition

```php
<?php declare(strict_types=1);

namespace Netgrade\ExamplePlugin\Core\Content\Example;

use Shopware\Core\Framework\DataAbstractionLayer\EntityDefinition;
use Shopware\Core\Framework\DataAbstractionLayer\FieldCollection;
use Shopware\Core\Framework\DataAbstractionLayer\Field\IdField;
use Shopware\Core\Framework\DataAbstractionLayer\Field\StringField;
use Shopware\Core\Framework\DataAbstractionLayer\Field\BoolField;
use Shopware\Core\Framework\DataAbstractionLayer\Field\LongTextField;
use Shopware\Core\Framework\DataAbstractionLayer\Field\FkField;
use Shopware\Core\Framework\DataAbstractionLayer\Field\ManyToOneAssociationField;
use Shopware\Core\Framework\DataAbstractionLayer\Field\Flag\PrimaryKey;
use Shopware\Core\Framework\DataAbstractionLayer\Field\Flag\Required;
use Shopware\Core\Framework\DataAbstractionLayer\Field\Flag\ApiAware;
use Shopware\Core\Content\Media\MediaDefinition;

class ExampleDefinition extends EntityDefinition
{
    public const ENTITY_NAME = 'netgrade_example';

    public function getEntityName(): string
    {
        return self::ENTITY_NAME;
    }

    public function getEntityClass(): string
    {
        return ExampleEntity::class;
    }

    public function getCollectionClass(): string
    {
        return ExampleCollection::class;
    }

    protected function defineFields(): FieldCollection
    {
        return new FieldCollection([
            (new IdField('id', 'id'))
                ->addFlags(new Required(), new PrimaryKey(), new ApiAware()),
            
            (new StringField('name', 'name'))
                ->addFlags(new Required(), new ApiAware()),
            
            (new LongTextField('description', 'description'))
                ->addFlags(new ApiAware()),
            
            (new BoolField('active', 'active'))
                ->addFlags(new Required(), new ApiAware()),
            
            (new FkField('media_id', 'mediaId', MediaDefinition::class))
                ->addFlags(new ApiAware()),
            
            (new ManyToOneAssociationField('media', 'media_id', MediaDefinition::class, 'id', false))
        ]);
    }
}
```

### 9.2 Migration

```php
<?php declare(strict_types=1);

namespace Netgrade\ExamplePlugin\Migration;

use Doctrine\DBAL\Connection;
use Shopware\Core\Framework\Migration\MigrationStep;

class Migration1703300000CreateExampleTable extends MigrationStep
{
    public function getCreationTimestamp(): int
    {
        return 1703300000;
    }

    public function update(Connection $connection): void
    {
        $sql = <<<SQL
CREATE TABLE IF NOT EXISTS `netgrade_example` (
    `id` BINARY(16) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `description` LONGTEXT NULL,
    `active` TINYINT(1) NOT NULL DEFAULT 1,
    `media_id` BINARY(16) NULL,
    `created_at` DATETIME(3) NOT NULL,
    `updated_at` DATETIME(3) NULL,
    PRIMARY KEY (`id`),
    KEY `idx.active` (`active`),
    CONSTRAINT `fk.netgrade_example.media_id`
        FOREIGN KEY (`media_id`) REFERENCES `media` (`id`)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
SQL;
        
        $connection->executeStatement($sql);
    }

    public function updateDestructive(Connection $connection): void
    {
        // Destruktive Änderungen (DROP, etc.)
    }
}
```

---

## 10. Shopware 6.7 Breaking Changes

### 10.1 Kritische Änderungen

| Bereich | Änderung | Impact |
|---------|----------|--------|
| **Build** | Webpack → Vite | Separate Plugin-Versionen für 6.6/6.7 |
| **Vue** | Vue 3 Kompatibilität entfernt | Nur native Vue 3 |
| **State** | Vuex → Pinia | `Shopware.State` → `Shopware.Store` |
| **Components** | sw-* → mt-* | Alle UI-Komponenten umbenannt |
| **Routing** | Annotations entfernt | Nur PHP 8 Attributes |
| **Caching** | Store-API Caching entfernt | Andere Caching-Strategie |
| **ESI** | Header/Footer via ESI | Template-Struktur geändert |

### 10.2 PHP Änderungen

```php
// Alle Properties müssen native Typen haben
// Vorher:
protected $myProperty;

// Nachher:
protected string $myProperty;
```

### 10.3 Vuex → Pinia Migration

```javascript
// Vorher (Vuex)
Shopware.State.get('cmsPageState');
Shopware.State.commit('cmsPageState/setPage', page);

// Nachher (Pinia)
Shopware.Store.get('cmsPage');
Shopware.Store.get('cmsPage').page = page;
```

---

## 11. Nützliche Commands

```bash
# Cache
ddev ssh
bin/console cache:clear

# Plugin Management
bin/console plugin:refresh
bin/console plugin:install -a NetgradeExamplePlugin
bin/console plugin:update -c -r -n NetgradeExamplePlugin
bin/console plugin:uninstall NetgradeExamplePlugin

# Datenbank
bin/console database:migrate
bin/console database:create-migration -p NetgradeExamplePlugin --name CreateExampleTable
bin/console database:migrate-destructive NetgradeExamplePlugin --all

# Theme
bin/console theme:compile
bin/console theme:change --all Storefront

# Admin/Storefront Builds (innerhalb Plugin-Verzeichnis)
./bin/build-administration.sh
./bin/build-storefront.sh
./bin/watch-administration.sh
./bin/watch-storefront.sh

# Assets
bin/console assets:install

# Scheduled Tasks
bin/console scheduled-task:register
bin/console scheduled-task:run
bin/console scheduled-task:run-single swag.cleanup_old_data

# System
bin/console system:update:prepare
bin/console system:update:finish

# DDEV spezifisch
ddev start
ddev stop
ddev ssh
```

---

## 12. Weiterführende Links

### Offizielle Dokumentation
- [Developer Docs](https://developer.shopware.com/docs/) - Hauptdokumentation
- [GitHub Repository](https://github.com/shopware/shopware)
- [Upgrade Guide 6.7](https://github.com/shopware/shopware/blob/trunk/UPGRADE-6.7.md)
- [Release Info 6.7](https://github.com/shopware/shopware/blob/trunk/RELEASE_INFO-6.7.md)

### Komponenten & UI
- [Meteor Component Library](https://meteor.shopware.com/) - UI Komponenten
- [Shopware UI](https://shopware.github.io/meteor-admin-sdk/) - Admin SDK

### Frameworks
- [Symfony Docs](https://symfony.com/doc/current/)
- [Vue 3 Docs](https://vuejs.org/guide/)
- [Pinia Docs](https://pinia.vuejs.org/)
- [Twig Docs](https://twig.symfony.com/doc/)

### Community
- [Shopware Community Discord](https://chat.shopware.com)
- [Shopware Forum](https://forum.shopware.com)

---

*Diese Dokumentation wurde für das Netgrade Demo Umgebung Projekt erstellt.*
*Shopware Version: 6.7.x*

---

## 13. Storefront Assets Build-Prozess (Shopware 6.7+)

### 13.1 WICHTIG: theme:compile baut KEINE Plugin-JavaScript-Dateien!

**Kritisches Missverständnis:** `theme:compile` kompiliert nur Theme-SCSS/Styles, **nicht** Plugin-JavaScript-Dateien.

| Build-Befehl | Was wird gebaut |
|--------------|-----------------|
| `theme:compile` | Nur Theme-SCSS/CSS (kein Plugin-JS!) |
| `bin/build-storefront.sh` | Storefront Core + alle Plugins (mit Webpack) |
| `shopware-cli extension build` | Einzelnes Plugin (mit ESBuild) |

### 13.2 Korrekte Plugin-Struktur für Storefront Assets

```
PluginName/
├── src/
│   └── Resources/
│       └── app/
│           └── storefront/
│               ├── src/                    # Source-Dateien
│               │   ├── main.js            # Entry Point (REQUIRED)
│               │   ├── plugin/
│               │   │   └── my-plugin.plugin.js
│               │   └── scss/
│               │       └── base.scss
│               ├── dist/                  # Kompilierte Assets (wird ausgeliefert!)
│               │   └── storefront/
│               │       └── js/
│               │           └── plugin-name/
│               │               └── plugin-name.js
│               └── package.json           # Optional: npm Dependencies
```

### 13.3 Build-Optionen für Plugin-Assets

#### Option A: shopware-cli (Empfohlen für 6.7+)

```bash
# Installation: https://developer.shopware.com/docs/products/cli/
brew install shopware/tap/shopware-cli  # macOS

# Build des Plugins (nutzt ESBuild - schneller)
shopware-cli extension build ./custom/plugins/MeinPlugin

# Mit Konfiguration (.shopware-extension.yml)
```

**.shopware-extension.yml:**
```yaml
build:
  zip:
    assets:
      enable_es_build_for_admin: true
      enable_es_build_for_storefront: true
```

#### Option B: Traditioneller Shopware Build

```bash
# Baut Storefront Core + alle Plugins
./bin/build-storefront.sh

# Dann Assets installieren
bin/console assets:install
```

#### Option C: Nur Theme kompilieren (nutzt vorhandene dist/)

```bash
# Schnellste Variante - nutzt bereits kompilierte dist/
# Die dist/ Dateien müssen bereits im Plugin sein!
bin/console theme:compile
```

### 13.4 Storefront vs. Administration Build-Tools

| Bereich | Build-Tool in 6.7 | Config-Datei |
|---------|-------------------|--------------|
| **Storefront** | Webpack/ESBuild (unchanged) | `webpack.config.js` (optional) |
| **Administration** | **Vite** (neu ab 6.7) | `vite.config.mts` |

**⚠️ Achtung:** Nur die Administration wurde auf Vite umgestellt! Die Storefront verwendet weiterhin Webpack.

### 13.5 main.js Entry Point (Storefront)

```javascript
// src/Resources/app/storefront/src/main.js
import MyPlugin from './plugin/my-plugin.plugin';

const PluginManager = window.PluginManager;

// Synchrone Registrierung
PluginManager.register('MyPlugin', MyPlugin, '[data-my-plugin]');

// Lazy Loading (für bessere Performance)
PluginManager.register('HeavyPlugin', () => import('./heavy-plugin/heavy-plugin.plugin'), '[data-heavy-plugin]');

// Hot Module Replacement
if (module.hot) {
    module.hot.accept();
}
```

### 13.6 Für Endkunden: Vorkompilierte Assets

**Best Practice:** Plugins sollten vorkompilierte Assets im `dist/` Verzeichnis mitliefern:

1. **Entwickler** baut das Plugin mit `shopware-cli` oder `build-storefront.sh`
2. **Die dist/ Dateien** werden committed und im Repository mitgeliefert
3. **Endkunde** installiert das Plugin und führt nur `theme:compile` aus

```bash
# Für Endkunden (Production) - Einfach!
bin/console plugin:install MeinPlugin
bin/console plugin:activate MeinPlugin
bin/console theme:compile  # Nutzt die mitgelieferten dist/ Dateien
```

### 14.4 Composer vs. custom/plugins - Wichtiger Unterschied

**Kritisch:** Prüfe immer, aus welchem Pfad das Plugin wirklich läuft!

```bash
# Prüfe, ob Plugin aus Composer oder custom/plugins läuft
ddev exec bin/console plugin:list

# Oder direkt in der Datenbank:
ddev mysql -e "SELECT name, managed_by_composer, path FROM plugin WHERE name LIKE '%widerruf%'"
```

| Quelle | Pfad | Managed by Composer |
|--------|------|---------------------|
| **Composer (path repo)** | `vendor/netgrade/widerrufsbutton/` → Symlink zu `custom/static-plugins/NetgradeWiderrufsbutton/` | `1` |
| **Lokal** | `custom/plugins/NetgradeWiderrufsbutton/` | `0` |

**Bei Path Repos (`"type":"path","url":"custom/static-plugins/*"`):** `vendor/` ist ein Symlink – Änderungen in `custom/static-plugins/` sind sofort in `vendor/` sichtbar. Für `composer.json`-Änderungen (z. B. plugin-icon) trotzdem `composer update netgrade/pluginname` ausführen, damit `installed.json` aktualisiert wird.

**Wenn `managed_by_composer = 1`:**
- Änderungen in der Quelldatei (custom/static-plugins oder vendor) reichen
- Für composer.json: `composer update` + `plugin:refresh` (siehe 14.20)

**Best Practice für Entwicklung:**
```bash
# Plugin aus Composer entfernen, lokale Version nutzen
composer remove netgrade/widerrufsbutton
# Dann aus custom/plugins installieren
bin/console plugin:install NetgradeWiderrufsbutton
```

---

### 14.5 Null-Safe in Twig-Templates (Email-Templates)

**Problem:** Twig crasht bei `null` Werten:
```twig
{# CRASH: Impossible to access attribute ("letterName") on a null variable #}
{{ widerrufsbelehrung.salutation.letterName }}
```

**Lösung:** Null-Check vor dem Zugriff:
```twig
{# KORREKT: Null-safe mit ternary operator #}
{{ widerrufsbelehrung.salutation is not null ? widerrufsbelehrung.salutation.letterName : '' }}

{# ODER: Null-Coalescing Operator (??) #}
{{ widerrufsbelehrung.salutation.letterName ?? '' }}
```

**Anwendung in Email-Templates:**
```twig
<p>Sehr geehrte/r 
    {{ widerrufsbelehrung.salutation is not null ? widerrufsbelehrung.salutation.letterName : '' }} 
    {{ widerrufsbelehrung.firstName }} 
    {{ widerrufsbelehrung.lastName }},
</p>
```

---

### 14.6 FormCmsHandler Konflikte vermeiden

**Problem:** Shopwares `FormCmsHandler` greift auf Custom-Formulare zu, wenn die Klasse `cms-element-form` verwendet wird.

```twig
{# FALSCH: FormCmsHandler verarbeitet das Formular zusätzlich #}
<div class="cms-element-form" data-form-cms-handler="true">
    <form>...</form>
</div>
```

**Lösung:** Eigene CSS-Klasse verwenden:
```twig
{# KORREKT: Nur eigenes Plugin verarbeitet das Formular #}
<div class="cms-element-netgrade-widerrufsformular">
    <form data-widerrufs-form="true">...</form>
</div>
```

**Zusätzlicher Schutz im JS:**
```javascript
// Submit-Event hart abfangen
_handleSubmit(event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    
    // Double-Submit verhindern
    if (this.isSubmitting) return;
    this.isSubmitting = true;
    
    // ... Rest der Logik
}
```

---

### 14.7 Step-Indikator: Scope-Problem beheben

**Problem:** Step-Indikator außerhalb des Formulars, JS sucht innerhalb:
```javascript
// FALSCH: Sucht nur im Formular
const step1 = this.el.querySelector('.step-1'); // null, weil außerhalb
```

**Lösung:** Im gemeinsamen Parent suchen:
```javascript
// KORREKT: Sucht im gemeinsamen Wrapper
_showStep(step) {
    const indicatorRoot = this.el.closest('.widerruf-form-wrapper');
    const step1 = indicatorRoot.querySelector('.step-1');
    const step2 = indicatorRoot.querySelector('.step-2');
    const step3 = indicatorRoot.querySelector('.step-3');
    // ...
}
```

---

### 14.8 Step-Farben korrekt definieren

| Zustand | Klasse | Farbe |
|---------|--------|-------|
| Aktiv (current) | `.active` | Blau |
| Abgeschlossen | `.completed` | Grün |
| Fehler | `.error` | Rot |

**Step 3 bei Erfolg = Grün (completed):**
```javascript
if (response.type === 'success') {
    // Step 1 & 2: completed (grün)
    // Step 3: completed (grün) - NICHT active (blau)
    this._showStep(3, 'completed');
}
```

**Step 3 bei Fehler = Rot (error):**
```javascript
if (response.type === 'warning') {
    // Widerruf gespeichert, aber Mail fehlgeschlagen
    this._showStep(3, 'error');
}
```

---

### 14.9 node_modules in .gitignore

**Wichtig:** `node_modules` niemals ins Git-Repository committen!

```bash
# .gitignore
/node_modules/
/vendor/
/var/
/public/theme/
/public/bundles/
```

**Wenn node_modules bereits im Repo:**
```bash
# Entfernen und in .gitignore aufnehmen
git rm -r --cached node_modules
echo "/node_modules/" >> .gitignore
git add .gitignore
git commit -m "Remove node_modules from repository"
```

---

## 14. Praktische Learnings & Best Practices (Session-Notizen)

> **Hinweis:** Dieser Abschnitt enthält praktische Erfahrungen aus der Plugin-Entwicklung für Shopware 6.7.

---

### 14.10 CSRF-Tokens in Shopware 6.5+ (WICHTIG!)

**Ab Shopware 6.5 wurden CSRF-Tokens komplett aus dem Storefront entfernt!**

| Version | CSRF-Handling |
|---------|---------------|
| **6.4 und älter** | `{{ sw_csrf('route.name') }}` in Twig |
| **6.5+ (inkl. 6.7)** | **Keine CSRF-Tokens mehr** - Schutz via SameSite-Cookies |

**Falsch (veraltet):**
```twig
{# Diese Funktionen existieren NICHT mehr in 6.7! #}
{{ sw_csrf('frontend.widerruf.submit') }}
{{ csrf_field() }}
{{ csrf_token('route.name') }}
```

**Richtig (Shopware 6.7):**
```twig
{# Einfach KEIN CSRF-Token im Formular #}
<form action="{{ path('frontend.widerruf.submit') }}" method="POST">
    {# Formularfelder #}
    <button type="submit">Absenden</button>
</form>
```

**Referenz:** [Shopware ADR - Deprecate Storefront CSRF](https://developer.shopware.com/docs/resources/references/adr/2022-11-16-deprecate-csrf.html)

---

### 14.11 CMS-Elemente: Kritische Registrierungs-Reihenfolge

**Häufigster Fehler:** CMS-Elemente importieren Komponenten, registrieren sie aber nicht!

**FALSCH (Element wird nicht im Admin angezeigt):**
```javascript
// elements/my-element/index.js
import './component';      // Nur importiert, nicht registriert!
import './config';         // Nur importiert, nicht registriert!
import './preview';        // Nur importiert, nicht registriert!

Shopware.Service('cmsService').registerCmsElement({
    name: 'my-element',
    component: 'sw-cms-el-my-element',  // ← Komponente existiert nicht!
    // ...
});
```

**RICHTIG (Working Pattern aus NetgradeAccordionElement):**
```javascript
// elements/my-element/index.js

// 1. Zuerst ALLE Komponenten registrieren
Shopware.Component.register('sw-cms-el-preview-my-element', () => import('./preview'));
Shopware.Component.register('sw-cms-el-config-my-element', () => import('./config'));
Shopware.Component.register('sw-cms-el-my-element', () => import('./component'));

// 2. DANN das Element registrieren
Shopware.Service('cmsService').registerCmsElement({
    name: 'my-element',
    label: 'sw-cms.elements.myElement.label',
    component: 'sw-cms-el-my-element',
    configComponent: 'sw-cms-el-config-my-element',
    previewComponent: 'sw-cms-el-preview-my-element',
    defaultConfig: {
        // ...
    }
});
```

---

### 14.12 CMS-Blöcke: Storefront-Templates nicht vergessen!

CMS-Blöcke brauchen **zwei** Template-Sätze:

1. **Admin-Templates** (für Layout-Editor):
   - `blocks/my-block/component/template.html.twig`
   - `blocks/my-block/preview/template.html.twig`

2. **Storefront-Templates** (für Frontend-Ausgabe):
   - `views/storefront/block/cms-block-my-block.html.twig` ← **Wird oft vergessen!**

**Storefront-Block-Template-Struktur:**
```twig
{# cms-block-my-block.html.twig #}
{% block block_my_block %}
    {% set element = block.slots.getSlot('content') %}

    <div class="col-12" data-cms-element-id="{{ element.id }}">
        {% block block_my_block_inner %}
            {% sw_include "@PluginName/storefront/element/cms-element-" ~ element.type ~ ".html.twig" ignore missing %}
        {% endblock %}
    </div>
{% endblock %}
```

**Wichtig:** Ohne das Storefront-Block-Template wird der Block im Frontend leer angezeigt (nur `cms-block-container-row row cms-row`)!

---

### 14.13 Controller für reine API/JSON-Antworten

Für Controller, die nur JSON zurückgeben (keine Twig-Templates rendern):

**Nicht erweitern:**
```php
// FALSCH - StorefrontController hat Twig-Abhängigkeiten
class MyController extends StorefrontController
{
    // Symfony versucht setTwig() aufzurufen
}
```

**Stattdessen:**
```php
// RICHTIG - Einfache Klasse ohne Twig-Abhängigkeit
use Symfony\Component\HttpFoundation\JsonResponse;

#[Route(defaults: [PlatformRequest::ATTRIBUTE_ROUTE_SCOPE => [StorefrontRouteScope::ID]])]
class MyController
{
    public function __construct(
        private MyService $myService,
        private DataValidator $dataValidator
    ) {}

    #[Route(path: '/api/action', name: 'frontend.api.action', methods: ['POST'])]
    public function action(Request $request): JsonResponse
    {
        // ...
        return new JsonResponse(['success' => true]);
    }
}
```

**services.xml:** Keine `setTwig()` oder `setContainer()` Calls für solche Controller!

---

### 14.14 Preview-Komponenten: SCSS nicht vergessen

**Pattern aus funktionierenden Plugins (NetgradeAccordionElement):**

```javascript
// preview/index.js
import template from './template.html.twig';
import './styles.scss';  // ← Wichtig!

export default {
    template,
};
```

**SCSS-Datei (preview/styles.scss):**
```scss
.sw-cms-el-preview-my-element {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 80px;
    padding: 16px;
    background-color: #e0aaaa;
    border-radius: 4px;

    &__title {
        font-size: 14px;
        font-weight: 600;
        color: #1a1a1a;
        text-align: center;
    }
}
```

**Farben für Preview:**
- Commerce/CTA-Elemente: Orange-Ton (`#ff6b35` - Netgrade Brand)
- Formular-Elemente: Blau-Ton (`#17a2b8`)
- Content-Elemente: Neutral (`#e0aaaa`)

---

### 14.15 Typo-Check: Slot-Namen und Element-Namen

**Kritischer Fehler:** Slot-Name passt nicht zu Element-Name

```javascript
// Block-Definition
slots: {
    content: 'netgrade-widerrufsbuton',  // ← Tippfehler! 'button' nicht 'buton'
}

// Element-Definition
Shopware.Service('cmsService').registerCmsElement({
    name: 'netgrade-widerrufsbutton',  // ← Korrekt
    // ...
});
```

**Empfehlung:** Immer Copy-Paste für Namen verwenden, nie abtippen!

---

### 14.16 services.xml: Autowiring-Probleme vermeiden

**Problem:** Symfony wirft Fehler wegen fehlender `setTwig()` Methode

**Ursache:** Controller wird als `autowire="true"` behandelt, hat aber keine Twig-Injection

**Lösung:** Explizite Service-Definition ohne Autowiring:
```xml
<service id="Netgrade\ExamplePlugin\Controller\Storefront\MyController" 
         public="true" 
         autowire="false" 
         autoconfigure="false">
    <argument type="service" id="Netgrade\ExamplePlugin\Service\MyService"/>
    <argument type="service" id="Shopware\Core\Framework\Validation\DataValidator"/>
    <tag name="controller.service_arguments"/>
</service>
```

---

### 14.17 E-Mail-Konfiguration über config.xml

**E-Mail-Templates im Plugin konfigurierbar machen:**

**WICHTIG – Sprachen explizit angeben:** Labels und HelpTexte in `config.xml` müssen `lang="de-DE"` und `lang="en-GB"` haben. Ohne explizites `de-DE` fällt Shopware auf Englisch zurück, auch wenn der Admin auf Deutsch eingestellt ist.

```xml
<!-- config.xml -->
<config>
    <card>
        <title lang="de-DE">E-Mail Konfiguration</title>
        <title lang="en-GB">Email Configuration</title>
        
        <input-field type="text">
            <name>adminEmail</name>
            <label lang="de-DE">Admin E-Mail Empfänger</label>
            <label lang="en-GB">Admin Email Recipient</label>
            <helpText lang="de-DE">E-Mail-Adresse für Admin-Benachrichtigungen</helpText>
            <helpText lang="en-GB">Email address for admin notifications</helpText>
            <defaultValue>admin@example.com</defaultValue>
        </input-field>
        
        <input-field type="single-select">
            <name>confirmationEmailTemplate</name>
            <label lang="de-DE">Kunden E-Mail Template</label>
            <label lang="en-GB">Customer Email Template</label>
            <options>
                <option>
                    <id>widerruf_confirmation</id>
                    <name>Widerruf Bestätigung</name>
                </option>
            </options>
        </input-field>
    </card>
</config>
```

**Zugriff im Service:**
```php
$adminEmail = $this->systemConfigService->get('NetgradeWiderrufsbutton.config.adminEmail');
```

---

### 14.18 Zwei-Agenten-Entwicklungsprozess

**Empfohlener Workflow für komplexe Plugins:**

1. **Implementierungs-Agent:** Setzt den Code um
2. **Review-Agent:** Prüft gegen Best Practices und Shopware-Doku

**Vorteile:**
- Frühe Fehlererkennung
- Wissenstransfer zwischen Agenten
- Qualitätssicherung

**Kritische Prüfpunkte beim Review:**
- ✅ Shopware 6.7 Kompatibilität (Meteor Components)
- ✅ CMS-Element Registrierung korrekt?
- ✅ Storefront-Templates vorhanden?
- ✅ CSRF-Tokens entfernt (6.5+)?
- ✅ PHP 8 native Types?

---

### 14.19 Debugging-Checkliste

**Problem: CMS-Element/Block wird nicht angezeigt**

1. `bin/console cache:clear`
2. `./bin/build-administration.sh` ausführen
3. Browser Hard-Reload (Strg+F5)
4. Prüfen: `Shopware.Component.register()` vor `registerCmsElement()`?
5. Prüfen: Alle Template-Dateien vorhanden?

**Problem: Block im Frontend leer**

1. Storefront-Block-Template vorhanden? (`cms-block-*.html.twig`)
2. Theme neu kompilieren: `bin/console theme:compile`
3. Slot-Name in Block-Definition korrekt?

**Problem: Controller wirft Twig-Fehler**

1. Controller erweitert `StorefrontController`?
2. Wenn nur JSON: Nicht von `StorefrontController` erweitern!
3. services.xml: `setTwig()` entfernen

---

### 14.20 Plugin-Icon nach Änderung sichtbar machen

**Problem:** Nach Änderung von `plugin-icon` in `composer.json` oder Hinzufügen einer Icon-Datei wird das Icon im Admin unter „Erweiterungen“ nicht angezeigt.

**`cache:clear` reicht nicht aus!** Shopware speichert das Icon beim Plugin-Refresh in der Datenbank. Die Composer-Metadaten müssen zuerst aktualisiert werden:

```bash
# 1. Composer-Metadaten aktualisieren (liest composer.json neu)
composer update netgrade/pluginname

# 2. Plugin-Liste aus Dateisystem in DB übertragen (inkl. Icon)
bin/console plugin:refresh

# 3. Optional: Cache leeren
bin/console cache:clear
```

**Ursache:** `PluginService` liest das Icon aus `vendor/.../plugin-icon-path` und speichert es als `iconRaw` in der Plugin-Tabelle. Ohne `composer update` bleibt die alte `installed.json`, ohne `plugin:refresh` wird die DB nicht aktualisiert.

---

### 14.21 Mail-Templates: Migration für bestehende Installationen

**Problem:** Eine Migration erstellt Mail-Templates nur bei **neuen** Installationen. Shops, die das Plugin bereits installiert haben, führen die Migration nicht erneut aus.

**Lösung:** Zusätzliche Migration, die **bestehende** `mail_template_translation`-Einträge per UPDATE anpasst:

- Templates über `mail_template_type.technical_name` finden (nicht über `system_config`)
- `content_html` und `content_plain` komplett ersetzen (robuster als String-Einfügungen)
- Für jede Sprache (`de-DE`/`en-GB`) das passende Template setzen

**Beispiel-Aufbau:**
```php
$typeId = $connection->fetchOne(
    'SELECT id FROM mail_template_type WHERE technical_name = :name',
    ['name' => 'netgrade_widerrufsbutton_confirmation']
);
$templates = $connection->fetchAllAssociative(
    'SELECT id FROM mail_template WHERE mail_template_type_id = :typeId',
    ['typeId' => $typeId]
);
// Pro Template: mail_template_translation per UPDATE anpassen
```

---

### 14.22 Mail-Template-Terminologie

**„Widerrufsbelehrung“ vs. „Widerruf“:**
- **Widerrufsbelehrung** = Rechtliche Belehrung (Information an den Kunden)
- **Widerruf** = Die eigentliche Handlung (Kunde widerruft den Vertrag)

In Kunden-Mails (Bestätigung, etc.) sollte **„Widerruf“** verwendet werden, z. B. „Bestätigung Ihres Widerrufs“, „vielen Dank für Ihren Widerruf“. „Widerrufsbelehrung“ ist in diesem Kontext sprachlich falsch.

---

### 14.23 Dateistruktur-Checkliste für CMS-Plugins

**Komplette Struktur für CMS-Element + Block:**

```
PluginName/
├── src/
│   ├── Resources/
│   │   ├── app/
│   │   │   └── administration/
│   │   │       └── src/
│   │   │           └── module/
│   │   │               └── sw-cms/
│   │   │                   ├── elements/
│   │   │                   │   └── my-element/
│   │   │                   │       ├── index.js              ← Component.register()!
│   │   │                   │       ├── component/
│   │   │                   │       │   ├── index.js
│   │   │                   │       │   └── template.html.twig
│   │   │                   │       ├── config/
│   │   │                   │       │   ├── index.js
│   │   │                   │       │   └── template.html.twig
│   │   │                   │       └── preview/
│   │   │                   │           ├── index.js          ← SCSS import!
│   │   │                   │           ├── template.html.twig
│   │   │                   │           └── styles.scss       ← Farben!
│   │   │                   └── blocks/
│   │   │                       └── my-block/
│   │   │                           ├── index.js
│   │   │                           ├── component/
│   │   │                           │   └── template.html.twig
│   │   │                           └── preview/
│   │   │                               ├── index.js
│   │   │                               ├── template.html.twig
│   │   │                               └── styles.scss
│   │   └── views/
│   │       └── storefront/
│   │           ├── element/
│   │           │   └── cms-element-my-element.html.twig
│   │           └── block/                      ← WIRD OFT VERGESSEN!
│   │               └── cms-block-my-block.html.twig
```

---

*Letzte Aktualisierung: 2026-02-18*
*Basierend auf praktischen Erfahrungen mit NetgradeWiderrufsbutton Plugin*
