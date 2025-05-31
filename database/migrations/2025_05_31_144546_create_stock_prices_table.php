<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('stock_prices', function (Blueprint $table) {
            $table->id();
            $table->foreignId('stock_id')->constrained()->onDelete('cascade');
            $table->uuid('uuid')->index();
            $table->dateTime('date')->index();
            $table->decimal('adj_close', 15, 6)->nullable();
            $table->decimal('close', 15, 6)->nullable();
            $table->decimal('high', 15, 6)->nullable();
            $table->decimal('low', 15, 6)->nullable();
            $table->decimal('open', 15, 6)->nullable();
            $table->bigInteger('volume')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('stock_prices');
    }
};
