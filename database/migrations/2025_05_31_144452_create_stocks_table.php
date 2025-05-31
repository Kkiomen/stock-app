<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('stocks', function (Blueprint $table) {
            $table->id();
            $table->string('ticker')->unique();
            $table->string('trends')->nullable();
            $table->string('name')->nullable(); // opcjonalnie: Apple Inc., Bitcoin itd.
            $table->timestamp('last_price_update')->nullable();
            $table->timestamp('last_image_update')->nullable();
            $table->timestamp('last_forecast_update')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('stocks');
    }
};
